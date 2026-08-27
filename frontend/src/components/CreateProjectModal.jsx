import React, { useState } from 'react';
import { FolderPlus } from 'lucide-react';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { createProject } from '../services/api';

export default function CreateProjectModal({
  isOpen,
  onClose,
  onProjectCreated
}) {
  const [name, setName] = useState('');
  const [folderPath, setFolderPath] = useState('');
  const [creating, setCreating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    try {
      const res = await createProject(name.trim(), folderPath.trim() || undefined);
      if (onProjectCreated) onProjectCreated(res.project_id);
      onClose();
    } catch (err) {
      alert('Creation failed: ' + err.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderPlus className="w-4 h-4 text-zinc-400" />
            <span>Create New Workspace</span>
          </DialogTitle>
          <DialogDescription>
            Create an isolated project workspace to ingest and reconcile document piles.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-3 text-xs">
          <div className="space-y-1">
            <label className="text-muted-foreground font-semibold">Workspace Name</label>
            <Input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Apex Horizon Phase 2"
            />
          </div>

          <div className="space-y-1">
            <label className="text-muted-foreground font-semibold">Document Folder (Optional)</label>
            <Input
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              placeholder="Leave blank for an empty workspace or enter folder path"
            />
          </div>
        </div>

        <DialogFooter>
          <Button type="button" onClick={onClose} variant="ghost" size="sm">
            Cancel
          </Button>
          <Button type="submit" disabled={creating || !name.trim()} size="sm">
            {creating ? 'Creating...' : 'Create Project'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}
