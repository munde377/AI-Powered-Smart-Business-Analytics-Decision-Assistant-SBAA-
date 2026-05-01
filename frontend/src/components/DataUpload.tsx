import { useState } from 'react'
import { uploadDataset } from '../services/api'

interface Props {
  token: string
}

export default function DataUpload({ token }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState('')

  const handleUpload = async () => {
    if (!file) return
    try {
      await uploadDataset(file, token)
      setMessage('Dataset uploaded successfully.')
    } catch (error) {
      setMessage('Upload failed. Check API connectivity and file type.')
    }
  }

  return (
    <section className="rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-slate-950/20">
      <h3 className="text-xl font-semibold text-white">Upload Dataset</h3>
      <p className="mt-2 text-slate-400">Import CSV or Excel files for automatic cleaning and analytics.</p>
      <div className="mt-4 flex flex-col gap-3">
        <input
          type="file"
          accept=".csv, application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
        />
        <button onClick={handleUpload} className="w-fit rounded bg-emerald-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-emerald-400">
          Upload Dataset
        </button>
        {message && <p className="text-sm text-slate-300">{message}</p>}
      </div>
    </section>
  )
}
