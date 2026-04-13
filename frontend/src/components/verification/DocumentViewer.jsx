import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ZoomIn,
  ZoomOut,
  RotateCw,
  Maximize2,
  FileText,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle
} from 'lucide-react';
import api from '../../services/api';
import './DocumentViewer.css';

const MIN_ZOOM = 25;
const MAX_ZOOM = 400;
const ZOOM_STEP = 10;

export const DocumentViewer = ({
  documentId,
  fileUrl,
  mimeType,
  onLoadError
}) => {
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [blobUrl, setBlobUrl] = useState(null);
  const [isPdf, setIsPdf] = useState(false);
  const [pdfPage, setPdfPage] = useState(1);
  const [pdfTotalPages, setPdfTotalPages] = useState(0);

  const containerRef = useRef(null);
  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const positionStart = useRef({ x: 0, y: 0 });

  // Check if document is PDF
  useEffect(() => {
    if (mimeType?.includes('pdf') || fileUrl?.toLowerCase().endsWith('.pdf')) {
      setIsPdf(true);
    } else {
      setIsPdf(false);
    }
  }, [mimeType, fileUrl]);

  // Fetch document as blob with auth
  const fetchDocument = useCallback(async () => {
    if (!documentId && !fileUrl) return;

    setIsLoading(true);
    setError(null);

    try {
      const url = fileUrl || `/api/documents/${documentId}/file/`;

      // Get auth token from localStorage or context
      const token = localStorage.getItem('access_token');

      const response = await fetch(url, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch document: ${response.status}`);
      }

      const blob = await response.blob();
      const url Blob = URL.createObjectURL(blob);

      // Cleanup previous blob URL
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }

      setBlobUrl(Blob);
    } catch (err) {
      setError(err.message);
      if (onLoadError) onLoadError(err);
    } finally {
      setIsLoading(false);
    }
  }, [documentId, fileUrl, blobUrl, onLoadError]);

  // Fetch on mount or when documentId/fileUrl changes
  useEffect(() => {
    fetchDocument();

    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [documentId, fileUrl]);

  // Handle zoom
  const handleZoomIn = () => {
    setZoom(z => Math.min(z + ZOOM_STEP, MAX_ZOOM));
  };

  const handleZoomOut = () => {
    setZoom(z => Math.max(z - ZOOM_STEP, MIN_ZOOM));
  };

  const handleFitWidth = () => {
    setZoom(100);
    setRotation(0);
    setPosition({ x: 0, y: 0 });
  };

  const handleZoom100 = () => {
    setZoom(100);
    setPosition({ x: 0, y: 0 });
  };

  const handleRotate = () => {
    setRotation(r => (r + 90) % 360);
  };

  // Mouse wheel zoom
  const handleWheel = (e) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      handleZoomIn();
    } else {
      handleZoomOut();
    }
  };

  // Pan handlers
  const handleMouseDown = (e) => {
    if (zoom > 100) {
      isDragging.current = true;
      dragStart.current = { x: e.clientX, y: e.clientY };
      positionStart.current = { ...position };
      e.preventDefault();
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging.current) {
      const dx = e.clientX - dragStart.current.x;
      const dy = e.clientY - dragStart.current.y;
      setPosition({
        x: positionStart.current.x + dx,
        y: positionStart.current.y + dy
      });
    }
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  // Reset position when zoom resets to fit
  useEffect(() => {
    if (zoom <= 100) {
      setPosition({ x: 0, y: 0 });
    }
  }, [zoom]);

  const isImage = mimeType?.startsWith('image/') ||
    (!isPdf && (mimeType?.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp)$/i.test(fileUrl || '')));

  return (
    <div className="document-viewer">
      {/* Toolbar */}
      <div className="viewer-toolbar">
        <div className="toolbar-group">
          <button
            onClick={handleZoomOut}
            disabled={zoom <= MIN_ZOOM}
            title="Zoom Out"
          >
            <ZoomOut size={18} />
          </button>
          <span className="zoom-display">{zoom}%</span>
          <button
            onClick={handleZoomIn}
            disabled={zoom >= MAX_ZOOM}
            title="Zoom In"
          >
            <ZoomIn size={18} />
          </button>
        </div>

        <div className="toolbar-group">
          <button onClick={handleRotate} title="Rotate 90°">
            <RotateCw size={18} />
          </button>
          <button onClick={handleFitWidth} title="Fit Width">
            <Maximize2 size={18} />
          </button>
          <button onClick={handleZoom100} title="100% (Original Size)">
            <FileText size={18} />
          </button>
        </div>
      </div>

      {/* Document Container */}
      <div
        ref={containerRef}
        className="viewer-container"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {isLoading && (
          <div className="viewer-loading">
            <Loader2 size={32} className="spinner" />
            <p>Loading document...</p>
          </div>
        )}

        {error && (
          <div className="viewer-error">
            <AlertCircle size={32} />
            <p>{error}</p>
            <button onClick={fetchDocument}>Retry</button>
          </div>
        )}

        {!isLoading && !error && blobUrl && (
          <>
            {isImage && (
              <div
                className="viewer-image-wrapper"
                style={{
                  transform: `scale(${zoom / 100}) rotate(${rotation}deg) translate(${position.x}px, ${position.y}px)`,
                  cursor: zoom > 100 ? 'grab' : 'default'
                }}
              >
                <img
                  src={blobUrl}
                  alt="Document"
                  draggable={false}
                />
              </div>
            )}

            {isPdf && (
              <div className="viewer-pdf-wrapper">
                {/* PDF.js placeholder - would need react-pdf to be installed */}
                <div className="pdf-placeholder">
                  <FileText size={48} />
                  <p>PDF Document</p>
                  <span>PDF rendering requires react-pdf library</span>
                  <a href={blobUrl} target="_blank" rel="noopener noreferrer" className="btn-open-pdf">
                    Open in new tab
                  </a>
                </div>

                {/* PDF Pagination */}
                {pdfTotalPages > 1 && (
                  <div className="pdf-pagination">
                    <button
                      onClick={() => setPdfPage(p => Math.max(1, p - 1))}
                      disabled={pdfPage <= 1}
                    >
                      <ChevronLeft size={18} />
                    </button>
                    <span>{pdfPage} / {pdfTotalPages}</span>
                    <button
                      onClick={() => setPdfPage(p => Math.min(pdfTotalPages, p + 1))}
                      disabled={pdfPage >= pdfTotalPages}
                    >
                      <ChevronRight size={18} />
                    </button>
                  </div>
                )}
              </div>
            )}

            {!isImage && !isPdf && (
              <div className="viewer-unsupported">
                <FileText size={48} />
                <p>Unsupported file type: {mimeType || 'unknown'}</p>
                <a href={blobUrl} target="_blank" rel="noopener noreferrer" className="btn-open">
                  Open in new tab
                </a>
              </div>
            )}
          </>
        )}

        {!isLoading && !error && !blobUrl && (
          <div className="viewer-empty">
            <FileText size={48} />
            <p>No document available</p>
          </div>
        )}
      </div>

      {/* Hint for pan/zoom */}
      {zoom > 100 && (
        <div className="viewer-hint">
          Click and drag to pan • Scroll to zoom
        </div>
      )}
    </div>
  );
};

export default DocumentViewer;