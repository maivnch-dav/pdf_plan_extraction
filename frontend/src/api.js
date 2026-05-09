const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000';
async function request(path, options = {}) { const res = await fetch(`${API_BASE}${path}`, options); if (!res.ok) throw new Error(await res.text()); return res.json(); }
export const loadSample = () => request('/demo/sample', { method: 'POST' });
export function uploadPdf(file){ const formData = new FormData(); formData.append('file', file); return request('/documents/upload', { method:'POST', body: formData }); }
export const getPeople = (documentId) => request(`/documents/${documentId}/people`);
export const getTasks = (personId) => request(`/people/${personId}/tasks`);
export const verifyTask = (taskId, verified) => request(`/tasks/${taskId}/verify`, { method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify({verified}) });
export const completeTask = (taskId, completed) => request(`/tasks/${taskId}/complete`, { method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify({completed}) });
export const getDashboard = (personId) => request(`/dashboard/${personId}`);
