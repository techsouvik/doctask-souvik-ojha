/**
 * Centralized API client for DocuMesh REST & SSE endpoints.
 */

const BASE_URL = '/api/v1';

export async function fetchProjects() {
  const res = await fetch(`${BASE_URL}/projects`);
  if (!res.ok) throw new Error('Failed to load projects');
  return res.json();
}

export async function createProject(projectName, docFolder) {
  const res = await fetch(`${BASE_URL}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_name: projectName, doc_folder: docFolder })
  });
  if (!res.ok) throw new Error('Failed to create project');
  return res.json();
}

export async function fetchProjectStatus(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/status`);
  if (!res.ok) throw new Error('Failed to get project status');
  return res.json();
}

export async function runPipeline(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to execute pipeline');
  return res.json();
}

export async function fetchDocuments(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function fetchDocumentDetail(projectId, docId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/documents/${docId}`);
  if (!res.ok) throw new Error('Failed to fetch document detail');
  return res.json();
}

export async function uploadDocument(projectId, file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/projects/${projectId}/documents`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload document');
  return res.json();
}

export async function fetchFindings(projectId, status = null) {
  const url = status ? `${BASE_URL}/projects/${projectId}/findings?status=${status}` : `${BASE_URL}/projects/${projectId}/findings`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch findings');
  return res.json();
}

export async function approveFinding(projectId, findingId, approved, feedback = null) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/findings/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ finding_id: findingId, approved, feedback })
  });
  if (!res.ok) throw new Error('Failed to update finding decision');
  return res.json();
}

export async function batchApproveFindings(projectId, approvedAll = true, decisions = null) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/findings/batch-approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_all: approvedAll, decisions })
  });
  if (!res.ok) throw new Error('Failed to batch approve findings');
  return res.json();
}

export async function fetchRegister(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/register`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch register');
  }
  return res.json();
}

export function exportReportUrl(projectId) {
  return `${BASE_URL}/projects/${projectId}/export-report`;
}

export async function fetchKnowledgeGraph(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/graph`);
  if (!res.ok) throw new Error('Failed to fetch knowledge graph');
  return res.json();
}

export async function fetchHistory(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/history`);
  if (!res.ok) throw new Error('Failed to fetch history checkpoints');
  return res.json();
}

export async function rewindToNode(projectId, targetNodeName, stateOverrides = null) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/rewind`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_node_name: targetNodeName, state_overrides: stateOverrides })
  });
  if (!res.ok) throw new Error('Failed to rewind graph state');
  return res.json();
}

export async function searchChunks(projectId, query, topK = 6) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK })
  });
  if (!res.ok) throw new Error('Failed to execute search');
  return res.json();
}

export async function listSessions(projectId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/sessions`);
  if (!res.ok) throw new Error('Failed to list sessions');
  return res.json();
}

export async function fetchSession(projectId, treeId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/sessions/${treeId}`);
  if (!res.ok) throw new Error('Failed to fetch session tree');
  return res.json();
}

export async function sendMessage(projectId, treeId, content, parentNodeId = null) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/sessions/${treeId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, parent_node_id: parentNodeId })
  });
  if (!res.ok) throw new Error('Failed to post message');
  return res.json();
}

export async function branchSession(projectId, treeId, parentNodeId, content) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/sessions/${treeId}/branch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ parent_node_id: parentNodeId, content })
  });
  if (!res.ok) throw new Error('Failed to branch session');
  return res.json();
}

export async function renameSession(projectId, treeId, title) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/sessions/${treeId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  });
  if (!res.ok) throw new Error('Failed to rename session');
  return res.json();
}

export async function deleteSession(projectId, treeId) {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/sessions/${treeId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete session');
  return res.json();
}

export async function fetchLLMSettings() {
  const res = await fetch(`${BASE_URL}/settings/llm`);
  if (!res.ok) throw new Error('Failed to get LLM settings');
  return res.json();
}

export async function updateLLMSettings(payload) {
  const res = await fetch(`${BASE_URL}/settings/llm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to update LLM settings');
  return res.json();
}

export async function testLLMConnection(payload) {
  const res = await fetch(`${BASE_URL}/settings/llm/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to test LLM connection');
  return res.json();
}

/**
 * Real Server-Sent Events (SSE) stream reader using Fetch ReadableStream
 */
export async function streamChatResponse(projectId, treeId, content, parentNodeId, callbacks) {
  const { onStage, onChunk, onAction, onDone, onError, onToolCall, onToolResult } = callbacks;

  try {
    const res = await fetch(`${BASE_URL}/projects/${projectId}/sessions/${treeId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({ content, parent_node_id: parentNodeId })
    });

    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.slice(6));
            if (data.type === 'stage' && onStage) {
              onStage(data.stage);
            } else if (data.type === 'tool_call' && onToolCall) {
              onToolCall(data);
            } else if (data.type === 'tool_result' && onToolResult) {
              onToolResult(data);
            } else if (data.type === 'chunk' && onChunk) {
              onChunk(data.content);
            } else if (data.type === 'action' && onAction) {
              onAction(data.action_payload);
            } else if (data.type === 'done' && onDone) {
              onDone(data);
            } else if (data.type === 'error' && onError) {
              onError(data.error);
            }
          } catch (err) {
            console.error('Error parsing SSE data line:', err, trimmed);
          }
        }
      }
    }
  } catch (err) {
    if (onError) onError(err.message || 'Stream connection error');
  }
}
