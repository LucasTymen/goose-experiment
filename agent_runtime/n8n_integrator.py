"""
N8N Integrator for GOOSE Agent Runtime
======================================

Integrates with N8N workflow engine for:
- Web scraping
- Automation
- External API calls
- Custom workflows
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime

from .config import N8NConfig, load_config

logger = logging.getLogger(__name__)


@dataclass
class N8NWorkflow:
    """Represents an N8N workflow"""
    id: str
    name: str
    description: str = ""
    active: bool = True
    webhook_path: Optional[str] = None
    nodes: List[Dict] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "active": self.active,
            "webhook_path": self.webhook_path,
            "nodes": self.nodes,
            "tags": self.tags
        }


@dataclass
class N8NExecution:
    """Represents an N8N workflow execution"""
    id: str
    workflow_id: str
    workflow_name: str
    status: str  # "running", "success", "failed", "waiting", "paused"
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error": self.error
        }


class N8NIntegrator:
    """
    Integrates GOOSE with N8N workflow engine.
    
    Features:
    - List available workflows
    - Execute workflows with parameters
    - Webhook management
    - Execution tracking
    - Error handling
    """
    
    def __init__(self, config: Optional[N8NConfig] = None):
        self.config = config or N8NConfig.from_env()
        self.base_url = self.config.get_base_url()
        self.api_key = self.config.api_key
        self.timeout = self.config.timeout
        
        # Cache for workflows
        self._workflows_cache: Optional[List[N8NWorkflow]] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 300  # 5 minutes
    
    async def get_workflows(self, force_refresh: bool = False) -> List[N8NWorkflow]:
        """
        Get list of available workflows from N8N.
        
        Args:
            force_refresh: If True, refresh the cache
            
        Returns:
            List of N8NWorkflow objects
        """
        if not force_refresh and self._workflows_cache and self._cache_time:
            cache_age = (datetime.utcnow() - self._cache_time).total_seconds()
            if cache_age < self._cache_ttl:
                return self._workflows_cache
        
        workflows = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                
                # Get all workflows
                url = f"{self.base_url}/api/v1/workflows"
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        workflows = [
                            N8NWorkflow(
                                id=w["id"],
                                name=w["name"],
                                description=w.get("description", ""),
                                active=w.get("active", True),
                                webhook_path=w.get("webhookPath"),
                                tags=w.get("tags", [])
                            )
                            for w in data.get("data", [])
                        ]
                        
                        # Cache results
                        self._workflows_cache = workflows
                        self._cache_time = datetime.utcnow()
                    else:
                        logger.error(f"Failed to get workflows: {response.status} - {await response.text()}")
        except Exception as e:
            logger.error(f"Error getting workflows: {e}")
        
        return workflows
    
    async def get_workflow(self, workflow_id: str) -> Optional[N8NWorkflow]:
        """Get a specific workflow by ID"""
        workflows = await self.get_workflows()
        for w in workflows:
            if w.id == workflow_id:
                return w
        return None
    
    async def find_workflows_by_tag(self, tag: str) -> List[N8NWorkflow]:
        """Find workflows by tag"""
        workflows = await self.get_workflows()
        return [w for w in workflows if tag in w.tags]
    
    async def find_workflows_by_name(self, name_pattern: str) -> List[N8NWorkflow]:
        """Find workflows by name pattern"""
        import re
        workflows = await self.get_workflows()
        pattern = re.compile(name_pattern, re.IGNORECASE)
        return [w for w in workflows if pattern.search(w.name)]
    
    async def execute_workflow(
        self,
        workflow_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = True,
        timeout: int = 60
    ) -> Optional[N8NExecution]:
        """
        Execute an N8N workflow.
        
        Args:
            workflow_id: The workflow ID to execute
            parameters: Optional parameters for the workflow
            wait_for_completion: If True, wait for execution to complete
            timeout: Maximum time to wait in seconds
            
        Returns:
            N8NExecution object or None if failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                
                # Build payload
                payload = {
                    "workflowId": workflow_id,
                    "mode": "start",
                }
                if parameters:
                    payload["startNodes"] = ["Start"]  # Default start node
                    payload["inputData"] = parameters
                
                # Execute workflow
                url = f"{self.base_url}/api/v1/executions"
                async with session.post(url, json=payload, headers=headers, timeout=self.timeout) as response:
                    if response.status == 201:
                        execution_data = await response.json()
                        execution_id = execution_data.get("id")
                        
                        if wait_for_completion and execution_id:
                            # Wait for completion
                            return await self._wait_for_execution(execution_id, timeout)
                        else:
                            # Return immediate execution info
                            return N8NExecution(
                                id=execution_id,
                                workflow_id=workflow_id,
                                workflow_name="",
                                status="running",
                                start_time=datetime.utcnow()
                            )
                    else:
                        logger.error(f"Failed to execute workflow: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            return None
    
    async def execute_workflow_by_name(
        self,
        workflow_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = True,
        timeout: int = 60
    ) -> Optional[N8NExecution]:
        """Execute a workflow by name"""
        workflows = await self.get_workflows()
        for w in workflows:
            if w.name == workflow_name:
                return await self.execute_workflow(w.id, parameters, wait_for_completion, timeout)
        
        logger.error(f"Workflow not found: {workflow_name}")
        return None
    
    async def _wait_for_execution(
        self,
        execution_id: str,
        timeout: int = 60
    ) -> Optional[N8NExecution]:
        """Wait for workflow execution to complete"""
        start_time = datetime.utcnow()
        
        while True:
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                logger.warning(f"Execution {execution_id} timed out after {timeout}s")
                return None
            
            # Check execution status
            execution = await self._get_execution(execution_id)
            if execution:
                if execution.status in ["success", "failed"]:
                    return execution
                elif execution.status in ["running", "waiting", "paused"]:
                    # Wait and retry
                    await asyncio.sleep(1)
                else:
                    return execution
            else:
                await asyncio.sleep(1)
    
    async def _get_execution(self, execution_id: str) -> Optional[N8NExecution]:
        """Get execution status"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                url = f"{self.base_url}/api/v1/executions/{execution_id}"
                
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return N8NExecution(
                            id=execution_id,
                            workflow_id=data.get("workflowId", ""),
                            workflow_name=data.get("workflowName", ""),
                            status=data.get("status", "unknown"),
                            start_time=datetime.fromisoformat(data.get("startedAt").replace("Z", "+00:00")) if data.get("startedAt") else datetime.utcnow(),
                            end_time=datetime.fromisoformat(data.get("stoppedAt").replace("Z", "+00:00")) if data.get("stoppedAt") else None,
                            result=data.get("data"),
                            error=data.get("error")
                        )
                    else:
                        logger.error(f"Failed to get execution: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting execution {execution_id}: {e}")
            return None
    
    async def execute_webhook(
        self,
        webhook_path: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a workflow via webhook.
        
        Args:
            webhook_path: The webhook path (e.g., "job-scraper")
            parameters: Parameters to pass to the webhook
            
        Returns:
            Response from the webhook
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/webhook/{webhook_path}"
                
                async with session.post(url, json=parameters, timeout=self.timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Webhook failed: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error calling webhook {webhook_path}: {e}")
            return None
    
    async def create_scraping_workflow(
        self,
        name: str,
        url: str,
        extract_fields: List[str],
        description: str = ""
    ) -> Optional[str]:
        """
        Create a basic web scraping workflow in N8N.
        
        Args:
            name: Name for the workflow
            url: URL to scrape
            extract_fields: List of fields to extract (CSS selectors or XPath)
            description: Workflow description
            
        Returns:
            Workflow ID if successful, None otherwise
        """
        # Build workflow JSON
        workflow_json = self._build_scraping_workflow(name, url, extract_fields, description)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                url = f"{self.base_url}/api/v1/workflows"
                
                async with session.post(url, json=workflow_json, headers=headers, timeout=self.timeout) as response:
                    if response.status == 201:
                        data = await response.json()
                        return data.get("id")
                    else:
                        logger.error(f"Failed to create workflow: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error creating scraping workflow: {e}")
            return None
    
    def _build_scraping_workflow(
        self,
        name: str,
        url: str,
        extract_fields: List[str],
        description: str
    ) -> Dict[str, Any]:
        """Build a workflow JSON for web scraping"""
        # Generate workflow ID
        workflow_id = f"scraper_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Build nodes
        nodes = [
            # Start node
            {
                "parameters": {},
                "id": f"{workflow_id}_start",
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [250, 300]
            },
            
            # HTTP Request node
            {
                "parameters": {
                    "method": "GET",
                    "url": url,
                    "options": {}
                },
                "id": f"{workflow_id}_http",
                "name": "HTTP Request",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 2,
                "position": [450, 300]
            },
            
            # HTML Extract node
            {
                "parameters": {
                    "options": {
                        "extract": "text"
                    }
                },
                "id": f"{workflow_id}_html",
                "name": "HTML",
                "type": "n8n-nodes-base.htmlExtract",
                "typeVersion": 1,
                "position": [650, 300]
            },
            
            # Code node for field extraction
            {
                "parameters": {
                    "jsCode": self._generate_extraction_code(extract_fields)
                },
                "id": f"{workflow_id}_code",
                "name": "Extract Fields",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [850, 300]
            },
            
            # Set node to output results
            {
                "parameters": {
                    "values": {
                        "string": [
                            {
                                "name": "data",
                                "value": "={{$json}}"
                            }
                        ]
                    }
                },
                "id": f"{workflow_id}_set",
                "name": "Set Output",
                "type": "n8n-nodes-base.set",
                "typeVersion": 2,
                "position": [1050, 300]
            }
        ]
        
        # Build connections
        connections = {
            f"{workflow_id}_start": {
                "main": [[f"{workflow_id}_http"]]
            },
            f"{workflow_id}_http": {
                "main": [[f"{workflow_id}_html"]]
            },
            f"{workflow_id}_html": {
                "main": [[f"{workflow_id}_code"]]
            },
            f"{workflow_id}_code": {
                "main": [[f"{workflow_id}_set"]]
            }
        }
        
        return {
            "name": name,
            "id": workflow_id,
            "description": description,
            "active": False,  # Start inactive for safety
            "settings": {
                "executionOrder": "v1"
            },
            "nodes": nodes,
            "connections": connections,
            "tags": ["scraper", "goose", "auto-generated"]
        }
    
    def _generate_extraction_code(self, fields: List[str]) -> str:
        """Generate JavaScript code for field extraction"""
        code = """
// Extract fields from HTML
const html = $input.all()[0].json;
const extracted = {};

// Define field extractors (CSS selectors)
const fieldSelectors = {
"""
        
        for i, field in enumerate(fields):
            code += f'    "{field}": "{field}"'
            if i < len(fields) - 1:
                code += ","
            code += "\n"
        
        code += """};

// Extract each field
for (const [field, selector] of Object.entries(fieldSelectors)) {
    try {
        // Use Cheerio for extraction (N8N has Cheerio available)
        const $ = cheerio.load(html);
        const result = $(selector).text().trim();
        if (result) {
            extracted[field] = result;
        }
    } catch (e) {
        // Fallback: try simple string search
        if (html.includes(selector)) {
            extracted[field] = selector;
        }
    }
}

// Return extracted data
return [extracted];
"""
        return code
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for N8N API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers
    
    async def get_execution_results(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the results of a completed execution"""
        execution = await self._get_execution(execution_id)
        if execution and execution.status == "success":
            return execution.result
        return None
    
    async def get_execution_status(self, execution_id: str) -> Optional[str]:
        """Get the status of an execution"""
        execution = await self._get_execution(execution_id)
        if execution:
            return execution.status
        return None
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                url = f"{self.base_url}/api/v1/workflows/{workflow_id}/activate"
                
                async with session.patch(url, headers=headers, timeout=self.timeout) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error activating workflow {workflow_id}: {e}")
            return False
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                url = f"{self.base_url}/api/v1/workflows/{workflow_id}/deactivate"
                
                async with session.patch(url, headers=headers, timeout=self.timeout) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error deactivating workflow {workflow_id}: {e}")
            return False
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                url = f"{self.base_url}/api/v1/workflows/{workflow_id}"
                
                async with session.delete(url, headers=headers, timeout=self.timeout) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}")
            return False
    
    async def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all webhooks"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = self._get_headers()
                url = f"{self.base_url}/api/v1/webhooks"
                
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        logger.error(f"Failed to list webhooks: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error listing webhooks: {e}")
            return []
    
    def create_scraping_parameters(
        self,
        url: str,
        fields: Optional[List[str]] = None,
        depth: int = 1,
        follow_links: bool = False
    ) -> Dict[str, Any]:
        """
        Create standard parameters for web scraping.
        
        Args:
            url: URL to scrape
            fields: Optional list of fields to extract
            depth: Scraping depth
            follow_links: Whether to follow links
            
        Returns:
            Parameters dict for N8N workflow
        """
        return {
            "url": url,
            "fields": fields or ["title", "description", "requirements", "company", "location"],
            "depth": depth,
            "follow_links": follow_links,
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
_n8n_integrator: Optional[N8NIntegrator] = None


def get_n8n_integrator() -> N8NIntegrator:
    """Get or create the global N8N integrator instance"""
    global _n8n_integrator
    if _n8n_integrator is None:
        _n8n_integrator = N8NIntegrator()
    return _n8n_integrator
