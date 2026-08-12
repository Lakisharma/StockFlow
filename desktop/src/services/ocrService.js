/* global window, fetch, FormData, module */
/**
 * StockFlow AI Document OCR Scanner Service
 */
class OcrService {
  constructor() {
    this.uploadUrl = 'http://127.0.0.1:8000/ocr/api/scans/';
    this.baseUrl = 'http://127.0.0.1:8000/ocr/';
  }

  async uploadBillDocument(file) {
    try {
      const formData = new FormData();
      formData.append('document', file);

      const response = await fetch(this.uploadUrl, {
        method: 'POST',
        body: formData
      });
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      return { success: true, data: await response.json() };
    } catch (e) {
      console.error("[OcrService] Error uploading bill document:", e);
      return { success: false, error: e.message };
    }
  }

  async verifyOcrScan(scanId, verifiedData) {
    try {
      const response = await fetch(`${this.baseUrl}verify/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scan_id: scanId, verified_data: verifiedData })
      });
      return { success: response.ok, data: await response.json() };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}

const ocrService = new OcrService();
if (typeof window !== 'undefined') {
  window.ocrService = ocrService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ocrService;
}
