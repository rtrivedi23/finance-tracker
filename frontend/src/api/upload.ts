import client from './client'
import type { UploadResponse } from './types'

export async function uploadStatement(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await client.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}
