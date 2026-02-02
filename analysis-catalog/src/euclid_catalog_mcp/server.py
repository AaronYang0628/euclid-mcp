"""MCP server for Euclid catalog FITS file parsing."""

import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .fits_parser import FITSCatalogParser


# Create server instance
app = Server("euclid-catalog-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="parse_fits_catalog",
            description="Parse a FITS catalog file and return basic information including HDU structure, number of objects, and fields",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the FITS catalog file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_catalog_fields",
            description="Get detailed information about all fields/columns in the catalog including data types, units, and statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the FITS catalog file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_catalog_objects",
            description="Retrieve object/source data from the catalog with optional pagination and column filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the FITS catalog file"
                    },
                    "start": {
                        "type": "integer",
                        "description": "Starting row index (default: 0)",
                        "default": 0
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of objects to return (default: 100)",
                        "default": 100
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of column names to include (omit for all columns)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_catalog_statistics",
            description="Get statistical summary of the catalog including total objects, fields, and field types",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the FITS catalog file"
                    }
                },
                "required": ["file_path"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    try:
        if name == "parse_fits_catalog":
            file_path = arguments["file_path"]
            with FITSCatalogParser(file_path) as parser:
                info = parser.get_basic_info()
            return [TextContent(
                type="text",
                text=json.dumps(info, indent=2)
            )]

        elif name == "get_catalog_fields":
            file_path = arguments["file_path"]
            with FITSCatalogParser(file_path) as parser:
                fields = parser.get_fields()
            return [TextContent(
                type="text",
                text=json.dumps(fields, indent=2)
            )]

        elif name == "get_catalog_objects":
            file_path = arguments["file_path"]
            start = arguments.get("start", 0)
            limit = arguments.get("limit", 100)
            columns = arguments.get("columns")

            with FITSCatalogParser(file_path) as parser:
                objects = parser.get_objects(start=start, limit=limit, columns=columns)
            return [TextContent(
                type="text",
                text=json.dumps(objects, indent=2)
            )]

        elif name == "get_catalog_statistics":
            file_path = arguments["file_path"]
            with FITSCatalogParser(file_path) as parser:
                stats = parser.get_statistics()
            return [TextContent(
                type="text",
                text=json.dumps(stats, indent=2)
            )]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
