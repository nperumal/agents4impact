"""BigQuery agent for data queries and analysis."""

from typing import Any, Dict, List
from google.cloud import bigquery
from config import Config
from .base_agent import BaseAgent


class BigQueryAgent(BaseAgent):
    """Agent for interacting with Google BigQuery."""

    def __init__(self):
        """Initialize the BigQuery agent."""
        super().__init__(
            name="BigQuery Agent",
            description="Specialized agent for querying and analyzing data in Google BigQuery",
            instructions="""You are a BigQuery expert agent. Your role is to:
1. Help users query data from BigQuery datasets
2. Analyze query results and provide insights
3. Suggest optimizations for queries
4. List available datasets and tables
5. Provide schema information

Always ensure queries are safe and follow best practices.
Use standard SQL syntax for BigQuery.
Warn users about potentially expensive queries.""",
        )

        # Initialize BigQuery client
        # This will use ADC if available, or fall back to gcloud user credentials
        try:
            self.client = bigquery.Client(
                project=Config.GOOGLE_CLOUD_PROJECT,
                location=Config.BIGQUERY_LOCATION,
            )
        except Exception as e:
            print(f"Note: BigQuery client initialization: {e}")
            # Will be initialized when first used
            self.client = None

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get BigQuery-specific tools."""
        return [
            {
                "name": "list_datasets",
                "description": "List all available BigQuery datasets in the project",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "list_tables",
                "description": "List all tables in a specific dataset",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dataset_id": {
                            "type": "string",
                            "description": "The dataset ID to list tables from",
                        }
                    },
                    "required": ["dataset_id"],
                },
            },
            {
                "name": "get_table_schema",
                "description": "Get the schema information for a specific table",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dataset_id": {
                            "type": "string",
                            "description": "The dataset ID",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "The table ID",
                        },
                    },
                    "required": ["dataset_id", "table_id"],
                },
            },
            {
                "name": "execute_query",
                "description": "Execute a SQL query on BigQuery",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to execute",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 100)",
                            "default": 100,
                        },
                    },
                    "required": ["query"],
                },
            },
        ]

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute BigQuery tools."""
        # Lazy initialize client if needed
        if self.client is None:
            try:
                self.client = bigquery.Client(
                    project=Config.GOOGLE_CLOUD_PROJECT,
                    location=Config.BIGQUERY_LOCATION,
                )
            except Exception as e:
                return {"error": f"BigQuery authentication failed: {e}. Please run: gcloud auth application-default login"}
        
        try:
            if tool_name == "list_datasets":
                return self._list_datasets()

            elif tool_name == "list_tables":
                return self._list_tables(parameters["dataset_id"])

            elif tool_name == "get_table_schema":
                return self._get_table_schema(
                    parameters["dataset_id"], parameters["table_id"]
                )

            elif tool_name == "execute_query":
                return self._execute_query(
                    parameters["query"],
                    parameters.get("max_results", 100),
                )

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}

    def _list_datasets(self) -> Dict[str, Any]:
        """List all datasets."""
        try:
            datasets = list(self.client.list_datasets())
            print(datasets[0].dataset_id)
            print(datasets[0].full_dataset_id)
        except Exception as e:
            return {"error": f"Failed to list datasets: {e}"}
        #datasets = list(self.client.list_datasets())
        return {
            "datasets": [
                {
                    "dataset_id": dataset.dataset_id,
                    "full_dataset_id": dataset.full_dataset_id,
                }
                for dataset in datasets
            ],
            "success": True,
        }

    def _list_tables(self, dataset_id: str) -> Dict[str, Any]:
        """List tables in a dataset."""
        tables = list(self.client.list_tables(dataset_id))
        return {
            "dataset_id": dataset_id,
            "tables": [
                {
                    "table_id": table.table_id,
                    "table_type": table.table_type,
                    "num_rows": getattr(table, "num_rows", None),
                }
                for table in tables
            ],
            "success": True,
        }

    def _get_table_schema(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        """Get table schema."""
        table = self.client.get_table(f"{dataset_id}.{table_id}")
        return {
            "dataset_id": dataset_id,
            "table_id": table_id,
            "schema": [
                {
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description,
                }
                for field in table.schema
            ],
            "num_rows": table.num_rows,
            "size_bytes": table.num_bytes,
            "success": True,
        }

    def _execute_query(self, query: str, max_results: int = 100) -> Dict[str, Any]:
        """Execute a BigQuery SQL query."""
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=10 * 1024 * 1024 * 1024  # 10 GB limit
        )

        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result(max_results=max_results)

        rows = [dict(row) for row in results]

        return {
            "query": query,
            "total_rows": results.total_rows,
            "rows_returned": len(rows),
            "rows": rows,
            "bytes_processed": query_job.total_bytes_processed,
            "bytes_billed": query_job.total_bytes_billed,
            "success": True,
        }

