export async function generateKey(): Promise<CryptoKey> {
  return window.crypto.subtle.generateKey(
    {
      name: "AES-GCM",
      length: 256,
    },
    true,
    ["encrypt", "decrypt"]
  );
}

export async function encryptFile(
  file: File,
  key: CryptoKey
): Promise<Blob> {
  const arrayBuffer = await file.arrayBuffer();
  const iv = window.crypto.getRandomValues(new Uint8Array(12));

  const encrypted = await window.crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: iv,
    },
    key,
    arrayBuffer
  );

  const encryptedBytes = new Uint8Array(iv.length + encrypted.byteLength);
  encryptedBytes.set(iv);
  encryptedBytes.set(new Uint8Array(encrypted), iv.length);

  return new Blob([encryptedBytes], { type: "application/octet-stream" });
}

export async function exportKeyAsHex(key: CryptoKey): Promise<string> {
  const exported = await window.crypto.subtle.exportKey("raw", key);
  return Array.from(new Uint8Array(exported))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}