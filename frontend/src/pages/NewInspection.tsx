import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  X,
  ImageIcon,
  Loader2,
  CheckCircle,
  ScanLine,
  Cpu,
  FileSearch,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';
import { analyzeImage } from '../api/client';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp'];
const MAX_MB = 15;

const PIPELINE_STEPS = [
  { key: 'upload', icon: Upload, label: 'Uploading image' },
  { key: 'quality', icon: ImageIcon, label: 'Image quality check' },
  { key: 'ocr', icon: Cpu, label: 'Running OCR' },
  { key: 'extract', icon: FileSearch, label: 'Extracting declarations' },
  { key: 'compliance', icon: ShieldCheck, label: 'Compliance analysis' },
];

export default function NewInspection() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(-1);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const validateFile = (f: File): string | null => {
    if (!ALLOWED_TYPES.includes(f.type))
      return `Unsupported format. Use JPG, PNG, BMP, TIFF, or WebP.`;
    if (f.size > MAX_MB * 1024 * 1024)
      return `File too large. Maximum size is ${MAX_MB} MB.`;
    return null;
  };

  const setImageFile = (f: File) => {
    const err = validateFile(f);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setFile(f);
    const url = URL.createObjectURL(f);
    setPreview(url);
  };

  const removeFile = () => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setError(null);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setImageFile(f);
  }, []);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setImageFile(f);
  };

  const runAnalysis = async () => {
    if (!file) return;
    setAnalyzing(true);
    setError(null);

    try {
      // Simulate step progression
      const stepDelay = (ms: number) => new Promise((r) => setTimeout(r, ms));

      setCurrentStep(0);
      await stepDelay(300);
      setCurrentStep(1);
      await stepDelay(400);
      setCurrentStep(2);

      const result = await analyzeImage(file);

      setCurrentStep(3);
      await stepDelay(200);
      setCurrentStep(4);
      await stepDelay(200);

      navigate(`/analysis/${result.inspection_id}`, { state: { result } });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Analysis failed. Please check that the backend is running and try again.';
      setError(msg);
      setCurrentStep(-1);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">New Product Inspection</h2>
        <p className="text-sm mt-1" style={{ color: 'rgba(226,232,240,0.55)' }}>
          Upload a product label image to run OCR-based compliance analysis
        </p>
      </div>

      {/* Upload area */}
      <div
        className={`relative rounded-2xl border-2 border-dashed transition-all duration-200 ${
          dragging ? 'scale-[1.01]' : ''
        }`}
        style={{
          borderColor: dragging
            ? 'var(--color-gold-500)'
            : file
            ? 'rgba(110,231,183,0.4)'
            : 'rgba(212,175,55,0.25)',
          background: dragging
            ? 'rgba(212,175,55,0.05)'
            : 'rgba(17,32,64,0.5)',
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        {!file ? (
          <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
            <div
              className="w-20 h-20 rounded-full flex items-center justify-center mb-5"
              style={{ background: 'rgba(212,175,55,0.08)', border: '1px solid rgba(212,175,55,0.2)' }}
            >
              <Upload className="w-9 h-9" style={{ color: 'var(--color-gold-500)' }} />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Drop product image here</h3>
            <p className="text-sm mb-1" style={{ color: 'rgba(226,232,240,0.5)' }}>
              or click to browse files
            </p>
            <p className="text-xs mb-6" style={{ color: 'rgba(226,232,240,0.3)' }}>
              JPG, PNG, BMP, TIFF, WebP · max {MAX_MB} MB
            </p>
            <button
              className="btn-primary"
              onClick={() => fileInputRef.current?.click()}
            >
              Choose Image
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_TYPES.join(',')}
              className="hidden"
              onChange={onFileChange}
              id="file-upload-input"
            />
          </div>
        ) : (
          <div className="p-5">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-5 h-5" style={{ color: '#6ee7b7' }} />
              <span className="text-sm font-medium" style={{ color: '#6ee7b7' }}>
                Image selected
              </span>
              <span className="text-xs ml-auto" style={{ color: 'rgba(226,232,240,0.45)' }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </span>
              <button
                onClick={removeFile}
                className="p-1 rounded-lg transition-colors"
                style={{ color: 'rgba(252,165,165,0.7)' }}
                title="Remove image"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="rounded-xl overflow-hidden" style={{ maxHeight: '400px' }}>
              <img
                src={preview!}
                alt="Preview"
                className="w-full object-contain"
                style={{ maxHeight: '380px', background: '#111' }}
              />
            </div>
            <p className="text-xs mt-3 text-center" style={{ color: 'rgba(226,232,240,0.35)' }}>
              {file.name}
            </p>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div
          className="flex items-start gap-3 rounded-xl p-4"
          style={{
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.2)',
          }}
        >
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: '#fca5a5' }} />
          <div>
            <p className="text-sm font-medium" style={{ color: '#fca5a5' }}>
              Error
            </p>
            <p className="text-sm mt-0.5" style={{ color: 'rgba(252,165,165,0.8)' }}>
              {error}
            </p>
          </div>
        </div>
      )}

      {/* Analysis pipeline progress */}
      {analyzing && (
        <div className="glass-card p-6">
          <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--color-gold-500)' }} />
            Analysis in progress...
          </h4>
          <div className="space-y-3">
            {PIPELINE_STEPS.map((step, i) => {
              const Icon = step.icon;
              const done = i < currentStep;
              const active = i === currentStep;
              return (
                <div key={step.key} className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all"
                    style={{
                      background: done
                        ? 'rgba(110,231,183,0.15)'
                        : active
                        ? 'rgba(212,175,55,0.15)'
                        : 'rgba(255,255,255,0.04)',
                      border: done
                        ? '1px solid rgba(110,231,183,0.3)'
                        : active
                        ? '1px solid rgba(212,175,55,0.4)'
                        : '1px solid rgba(255,255,255,0.08)',
                    }}
                  >
                    {done ? (
                      <CheckCircle className="w-4 h-4" style={{ color: '#6ee7b7' }} />
                    ) : (
                      <Icon
                        className={`w-4 h-4 ${active ? 'animate-pulse' : ''}`}
                        style={{
                          color: active ? 'var(--color-gold-500)' : 'rgba(226,232,240,0.25)',
                        }}
                      />
                    )}
                  </div>
                  <span
                    className="text-sm"
                    style={{
                      color: done
                        ? '#6ee7b7'
                        : active
                        ? 'var(--color-gold-400)'
                        : 'rgba(226,232,240,0.35)',
                      fontWeight: active ? 600 : 400,
                    }}
                  >
                    {step.label}
                    {active && (
                      <span className="ml-2 text-xs" style={{ color: 'rgba(226,232,240,0.4)' }}>
                        running...
                      </span>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Analyze button */}
      <button
        className="btn-primary w-full flex items-center justify-center gap-2 py-3.5 text-base"
        onClick={runAnalysis}
        disabled={!file || analyzing}
        id="analyze-button"
      >
        {analyzing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <ScanLine className="w-5 h-5" />
            Analyze Product
          </>
        )}
      </button>

      <p className="text-xs text-center" style={{ color: 'rgba(226,232,240,0.3)' }}>
        Analysis may take 30–90 seconds on first run while OCR models load.
      </p>
    </div>
  );
}
