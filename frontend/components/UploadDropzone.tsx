"use client";

import { useRef, useState } from "react";

export function UploadDropzone({ onUpload }: { onUpload: (file: File) => Promise<void> }) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setBusy(true);
    try {
      for (const file of Array.from(files)) {
        await onUpload(file);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-md p-10 text-center cursor-pointer transition-colors
        ${dragging ? "border-brass bg-amber-bg" : "border-parchment-line bg-paper"}`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="application/pdf,image/jpeg,image/png,image/tiff,image/webp"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <p className="font-display text-lg mb-1">
        {busy ? "Uploading…" : "Drop client documents here"}
      </p>
      <p className="text-sm text-ink/60">Passports, I-797 notices, employment letters — PDF or image, up to 25MB each</p>
    </div>
  );
}
