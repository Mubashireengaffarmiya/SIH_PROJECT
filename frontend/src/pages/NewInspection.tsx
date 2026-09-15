import { useState, useCallback, useRef, useEffect } from 'react';
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
  ArrowRight,
  Package,
  Camera,
  Video,
  Check
} from 'lucide-react';
import { analyzeImage } from '../api/client';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp'];
const MAX_MB = 15;

const FLOW_STEPS = [
  { id: 1, label: 'Product Info' },
  { id: 2, label: 'Images' },
  { id: 3, label: 'Quality Check' },
  { id: 4, label: 'Analysis' },
  { id: 5, label: 'Review' },
  { id: 6, label: 'Report' }
];

export default function NewInspection() {
  const [activeStep, setActiveStep] = useState(1);
  const [productCategory, setProductCategory] = useState('');
  
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  
  // For the backend simulation
  const [backendStep, setBackendStep] = useState<number>(-1);
  const [error, setError] = useState<string | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const navigate = useNavigate();

  const validateFile = (f: File): string | null => {
    if (!ALLOWED_TYPES.includes(f.type))
      return `Unsupported format. Use JPG, PNG, BMP, TIFF, or WebP.`;
    if (f.size > MAX_MB * 1024 * 1024)
      return `File too large. Maximum size is ${MAX_MB} MB.`;
    return null;
  };

  const setImageFile = useCallback((f: File) => {
    const err = validateFile(f);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setFile(f);
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(f);
    });
  }, []);

  const removeFile = () => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setError(null);
  };

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraOpen(false);
  }, []);

  useEffect(() => {
    return () => {
      stopCamera();
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview, stopCamera]);

  const openCamera = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError('Camera capture is not supported in this browser.');
      return;
    }

    try {
      setCameraError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      streamRef.current = stream;
      setCameraOpen(true);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch {
      setCameraError('Unable to access the camera. Please allow camera permission or upload a file instead.');
      stopCamera();
    }
  };

  const captureFromCamera = () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setCameraError('Could not capture the camera image.');
      return;
    }

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) {
        setCameraError('The captured photo was empty. Please try again.');
        return;
      }

      const capturedFile = new File([blob], `capture-${Date.now()}.jpg`, { type: 'image/jpeg' });
      setImageFile(capturedFile);
      stopCamera();
    }, 'image/jpeg', 0.92);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setImageFile(f);
  }, [setImageFile]);

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

      setActiveStep(3); // Quality Check
      setBackendStep(0);
      await stepDelay(500);
      
      setActiveStep(4); // Analysis
      setBackendStep(1);
      await stepDelay(500);
      setBackendStep(2);

      const result = await analyzeImage(file);

      setBackendStep(3);
      await stepDelay(300);
      setBackendStep(4);
      await stepDelay(300);

      navigate(`/analysis/${result.inspection_id}`, {
        state: {
          result,
          previewUrl: preview,
        },
      });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Analysis failed. Please check that the backend is running and try again.';
      setError(msg);
      setBackendStep(-1);
      setActiveStep(2); // Revert to images step
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Stepper Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-6">New Product Inspection</h2>
        <div className="flex items-center justify-between relative">
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-slate-800 rounded-full z-0"></div>
          <div 
            className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full z-0 transition-all duration-500"
            style={{ width: `${((activeStep - 1) / (FLOW_STEPS.length - 1)) * 100}%` }}
          ></div>
          
          {FLOW_STEPS.map((step) => (
            <div key={step.id} className="relative z-10 flex flex-col items-center">
              <div 
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300 border-4 ${
                  activeStep > step.id 
                    ? 'bg-blue-500 border-slate-900 text-white' 
                    : activeStep === step.id 
                      ? 'bg-indigo-600 border-slate-900 text-white scale-110 shadow-lg shadow-indigo-500/50' 
                      : 'bg-slate-800 border-slate-900 text-slate-400'
                }`}
              >
                {activeStep > step.id ? <CheckCircle className="w-5 h-5" /> : step.id}
              </div>
              <span className={`absolute top-12 text-xs font-medium w-24 text-center ${
                activeStep >= step.id ? 'text-slate-200' : 'text-slate-500'
              }`}>
                {step.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-16 bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 backdrop-blur-sm">
        {activeStep === 1 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 bg-blue-500/10 rounded-xl">
                <Package className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white">Product Information</h3>
                <p className="text-slate-400 text-sm">Provide basic details to categorize the inspection</p>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Commodity Category</label>
              <select 
                className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                value={productCategory}
                onChange={(e) => setProductCategory(e.target.value)}
              >
                <option value="">Select a category (Optional)</option>
                <option value="food">Packaged Food & Beverages</option>
                <option value="cosmetics">Cosmetics & Toiletries</option>
                <option value="electronics">Electronics</option>
                <option value="hardware">Hardware & Tools</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div className="pt-4 flex justify-end">
              <button 
                onClick={() => setActiveStep(2)}
                className="btn-primary flex items-center gap-2 px-6 py-2.5"
              >
                Next Step <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {activeStep >= 2 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
             <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">Upload Images</h3>
                  <p className="text-slate-400 text-sm">Upload clear photos of the product labels</p>
                </div>
                {activeStep === 2 && (
                   <button 
                     onClick={() => setActiveStep(1)}
                     className="text-sm text-slate-400 hover:text-white"
                   >
                     ← Back to Info
                   </button>
                )}
             </div>

            <div className="flex flex-wrap gap-3 mb-4">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="btn-secondary flex items-center gap-2"
              >
                <Upload className="w-4 h-4" /> Upload file
              </button>
              <button
                type="button"
                onClick={openCamera}
                className="btn-secondary flex items-center gap-2"
              >
                <Camera className="w-4 h-4" /> Use camera
              </button>
            </div>

            {cameraOpen && (
              <div className="mb-5 rounded-2xl border border-slate-700 bg-slate-950/60 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 text-slate-200">
                    <Video className="w-4 h-4 text-blue-400" />
                    <span className="text-sm font-medium">Camera preview</span>
                  </div>
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="text-xs text-slate-300 hover:text-white"
                  >
                    Close
                  </button>
                </div>
                <video ref={videoRef} className="w-full rounded-xl bg-black" playsInline muted />
                <div className="mt-3 flex justify-center">
                  <button type="button" onClick={captureFromCamera} className="btn-primary flex items-center gap-2">
                    <Check className="w-4 h-4" /> Capture photo
                  </button>
                </div>
              </div>
            )}

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
                    {!analyzing && (
                      <button
                        onClick={removeFile}
                        className="p-1 rounded-lg transition-colors hover:bg-red-500/10"
                        style={{ color: 'rgba(252,165,165,0.7)' }}
                        title="Remove image"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                  <div className="rounded-xl overflow-hidden" style={{ maxHeight: '400px' }}>
                    <img
                      src={preview!}
                      alt="Preview"
                      className="w-full object-contain"
                      style={{ maxHeight: '380px', background: '#111' }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Error */}
            {(error || cameraError) && (
              <div className="flex items-start gap-3 rounded-xl p-4 bg-red-500/10 border border-red-500/20">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-400" />
                <div>
                  <p className="text-sm font-medium text-red-400">Error</p>
                  <p className="text-sm mt-0.5 text-red-300/80">{error ?? cameraError}</p>
                </div>
              </div>
            )}

            {/* Analysis pipeline progress */}
            {analyzing && (
              <div className="glass-card p-6 border border-slate-700/50 mt-6">
                <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                  Analysis in progress...
                </h4>
                <div className="space-y-4">
                  {[
                    { key: 'quality', icon: ImageIcon, label: 'Checking Image Quality' },
                    { key: 'ocr', icon: Cpu, label: 'Running OCR Engine' },
                    { key: 'extract', icon: FileSearch, label: 'Extracting Declarations' },
                    { key: 'compliance', icon: ShieldCheck, label: 'Applying Compliance Rules' },
                  ].map((step, i) => {
                    const Icon = step.icon;
                    const done = i < backendStep;
                    const active = i === backendStep;
                    return (
                      <div key={step.key} className="flex items-center gap-4">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                            done ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400' :
                            active ? 'bg-blue-500/20 border border-blue-500/50 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.5)]' :
                            'bg-slate-800/50 border border-slate-700 text-slate-500'
                          }`}
                        >
                          {done ? <CheckCircle className="w-5 h-5" /> : <Icon className={`w-5 h-5 ${active ? 'animate-pulse' : ''}`} />}
                        </div>
                        <div className="flex flex-col">
                           <span className={`text-sm font-medium ${done ? 'text-emerald-400' : active ? 'text-white' : 'text-slate-500'}`}>
                             {step.label}
                           </span>
                           {active && (
                             <span className="text-xs text-blue-400/80 mt-0.5 animate-pulse">Processing...</span>
                           )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Analyze button */}
            {activeStep === 2 && (
              <button
                className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-base shadow-lg shadow-blue-500/20 mt-6"
                onClick={runAnalysis}
                disabled={!file || analyzing}
                id="analyze-button"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing Label...
                  </>
                ) : (
                  <>
                    <ScanLine className="w-5 h-5" />
                    Run Compliance Analysis
                  </>
                )}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
