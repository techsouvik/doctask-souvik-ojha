import React, { useState, useEffect } from 'react';
import { 
  Key, 
  Cpu, 
  Globe, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  Eye, 
  EyeOff 
} from 'lucide-react';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { fetchLLMSettings, updateLLMSettings, testLLMConnection } from '../services/api';

export default function SettingsModal({ isOpen, onClose, onSaved }) {
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [modelName, setModelName] = useState('gpt-4o-mini');
  const [baseUrl, setBaseUrl] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      const data = await fetchLLMSettings();
      setProvider(data.provider || 'openai');
      setModelName(data.model_name || 'gpt-4o-mini');
      setBaseUrl(data.base_url || '');
      setTestResult(null);
    } catch (err) {
      console.error('Failed to load LLM settings:', err);
    }
  };

  const handleProviderChange = (newProv) => {
    setProvider(newProv);
    if (newProv === 'openai') {
      setModelName('gpt-4o-mini');
      setBaseUrl('');
    } else if (newProv === 'anthropic') {
      setModelName('claude-3-5-sonnet-20241022');
      setBaseUrl('');
    } else if (newProv === 'gemini') {
      setModelName('gemini-1.5-flash');
      setBaseUrl('');
    } else if (newProv === 'openai_compatible') {
      setModelName('llama3.2');
      setBaseUrl('http://localhost:11434/v1');
    }
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await testLLMConnection({
        provider,
        api_key: apiKey,
        model_name: modelName,
        base_url: baseUrl
      });
      setTestResult(res);
    } catch (err) {
      setTestResult({ success: false, message: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateLLMSettings({
        provider,
        api_key: apiKey || undefined,
        model_name: modelName,
        base_url: baseUrl
      });
      if (onSaved) onSaved();
      onClose();
    } catch (err) {
      alert('Save error: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-zinc-400" />
          <span>LLM Provider Configuration</span>
        </DialogTitle>
        <DialogDescription>
          Select an AI model provider or custom OpenAI-compatible endpoint for live chat streaming.
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-3.5 py-3 text-xs">
        {/* Provider Switcher */}
        <div className="space-y-1">
          <label className="text-muted-foreground font-semibold">Provider</label>
          <div className="grid grid-cols-2 gap-1.5">
            {[
              { id: 'openai', label: 'OpenAI (GPT-4o)' },
              { id: 'anthropic', label: 'Anthropic Claude' },
              { id: 'gemini', label: 'Google Gemini' },
              { id: 'openai_compatible', label: 'Ollama / Local vLLM' }
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => handleProviderChange(p.id)}
                className={`p-2 rounded-lg border text-left text-xs font-medium transition ${
                  provider === p.id
                    ? 'border-zinc-400 bg-zinc-800 text-foreground font-semibold'
                    : 'border-border bg-card text-muted-foreground hover:text-foreground'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Model ID */}
        <div className="space-y-1">
          <label className="text-muted-foreground font-semibold">Model Name</label>
          <Input
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            placeholder="e.g. gpt-4o-mini, llama3.2"
          />
        </div>

        {/* Base URL */}
        <div className="space-y-1">
          <label className="text-muted-foreground font-semibold">
            Base URL {provider === 'openai_compatible' ? '(Required)' : '(Optional)'}
          </label>
          <Input
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="e.g. http://localhost:11434/v1"
          />
        </div>

        {/* API Key */}
        <div className="space-y-1">
          <label className="text-muted-foreground font-semibold">API Key</label>
          <div className="relative">
            <Input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="pr-8"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Diagnostics message */}
        {testResult && (
          <div
            className={`p-2.5 rounded-lg border text-xs flex items-start gap-2 ${
              testResult.success
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            }`}
          >
            {testResult.success ? (
              <CheckCircle className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
            )}
            <p className="leading-snug">{testResult.message}</p>
          </div>
        )}
      </div>

      <DialogFooter className="flex items-center justify-between">
        <Button
          type="button"
          onClick={handleTestConnection}
          disabled={testing}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`w-3 h-3 mr-1 ${testing ? 'animate-spin' : ''}`} />
          <span>{testing ? 'Testing...' : 'Test Connection'}</span>
        </Button>

        <div className="flex items-center gap-2">
          <Button onClick={onClose} variant="ghost" size="sm">
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving} size="sm">
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </DialogFooter>
    </Dialog>
  );
}
