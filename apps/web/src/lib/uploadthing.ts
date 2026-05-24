import { generateReactHelpers } from "@uploadthing/react";
import { ourFileRouter } from "@/app/api/uploadthing/core";

export const { useUploadThing, uploadFiles } =
  generateReactHelpers<typeof ourFileRouter>();

export type UploadThingFile = {
  name: string;
  size: number;
  type: string;
  key: string;
  url: string;
  ufsUrl: string;
};

export async function deleteUploadthingFile(fileUrl: string): Promise<boolean> {
  try {
    const response = await fetch(
      `/api/uploadthing?fileUrl=${encodeURIComponent(fileUrl)}`,
      { method: "DELETE" }
    );
    return response.ok;
  } catch {
    return false;
  }
}