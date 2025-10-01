"""Command line entry point to export OneNote sections and populate a vector store."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from onenote_import.auth import DeviceCodeAuthenticator
from onenote_import.graph import GraphClient
from onenote_import.processors import html_to_text, slugify, write_text_file
from onenote_import.vectorstore import VectorStoreManager

DEFAULT_SCOPES = ["Notes.Read", "offline_access"]
PAUSE_AFTER_SECTIONS = 600
PAUSE_SECONDS = 300


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-id", required=True, help="Azure AD application (client) ID")
    parser.add_argument(
        "--tenant-id",
        default="common",
        help="Azure AD tenant ID or 'common' for multi-tenant apps",
    )
    parser.add_argument(
        "--output-dir",
        default=Path("data/sections"),
        type=Path,
        help="Directory where cleaned text files will be saved",
    )
    parser.add_argument(
        "--vectorstore",
        default=Path("vectorstore"),
        type=Path,
        help="Directory used by ChromaDB to persist embeddings",
    )
    parser.add_argument(
        "--collection",
        default="onenote-sections",
        help="Name of the Chroma collection to store embeddings",
    )
    parser.add_argument(
        "--pause-after",
        type=int,
        default=PAUSE_AFTER_SECTIONS,
        help="Pause duration trigger after processing this many sections",
    )
    parser.add_argument(
        "--pause-seconds",
        type=int,
        default=PAUSE_SECONDS,
        help="Number of seconds to pause after reaching the pause-after threshold",
    )
    parser.add_argument(
        "--scopes",
        nargs="*",
        default=DEFAULT_SCOPES,
        help="Microsoft Graph permission scopes for the device code flow",
    )
    parser.add_argument(
        "--embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model used to embed sections",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    scopes: list[str] = []
    passthrough_scopes = {"offline_access", "openid", "profile"}
    for scope in args.scopes:
        if scope.startswith("http"):
            scopes.append(scope)
        elif scope in passthrough_scopes:
            scopes.append(scope)
        else:
            scopes.append(f"https://graph.microsoft.com/{scope}")

    authenticator = DeviceCodeAuthenticator(
        client_id=args.client_id,
        tenant_id=args.tenant_id,
        scopes=scopes,
    )
    token = authenticator.acquire_token()
    access_token = token["access_token"]

    graph = GraphClient(access_token)
    vectorstore = VectorStoreManager(
        persist_directory=args.vectorstore,
        collection_name=args.collection,
        embedding_model=args.embedding_model,
    )

    processed_sections = 0

    for section in graph.iter_sections():
        section_id = section["id"]
        section_name = section.get("displayName", f"Section-{section_id}")
        section_slug = slugify(section_name, fallback="section")

        all_pages_text: list[str] = []
        for page in graph.iter_pages(section_id):
            page_content_html = graph.get_page_content(page["id"])
            cleaned = html_to_text(page_content_html)
            page_title = page.get("title", "Untitled page")
            all_pages_text.append(f"# {page_title}\n{cleaned}")

        combined_text = "\n\n".join(all_pages_text).strip()
        if not combined_text:
            print(f"Skipping empty section {section_name} ({section_id})")
            continue

        output_path = write_text_file(args.output_dir, f"{section_slug}-{section_id}", combined_text)
        vectorstore.add_document(
            document_id=section_id,
            text=combined_text,
            metadata={
                "section_id": section_id,
                "section_name": section_name,
                "file_path": str(output_path),
            },
        )

        processed_sections += 1
        print(f"Saved section '{section_name}' to {output_path}")

        if processed_sections % args.pause_after == 0:
            print(
                f"Processed {processed_sections} sections. Pausing for {args.pause_seconds} seconds to respect rate limits."
            )
            time.sleep(args.pause_seconds)

    print(f"Finished processing {processed_sections} sections.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
