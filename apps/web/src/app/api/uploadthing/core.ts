import { createUploadthing, type FileRouter } from "uploadthing/next";

export const uploadthingToken =
  process.env.UPLOADTHING_TOKEN ??
  getUploadThingTokenFromLegacyEnv();

const f = createUploadthing({
  errorFormatter: (error) => {
    console.error("Uploadthing error:", error);
    return {
      message: error.message,
      code: error.code,
    };
  },
});

function getUploadThingTokenFromLegacyEnv(): string | undefined {
  const apiKey = process.env.UPLOADTHING_SECRET;
  const appId = process.env.UPLOADTHING_APP_ID;
  if (!apiKey || !appId) return undefined;

  const rawRegions = process.env.UPLOADTHING_REGIONS;
  const regions = rawRegions
    ?.split(",")
    .map((region) => region.trim())
    .filter(Boolean);

  return Buffer.from(
    JSON.stringify({
      apiKey,
      appId,
      regions: regions && regions.length > 0 ? regions : ["us-east-1"],
    })
  ).toString("base64");
}

export const ourFileRouter = {
  contractUploader: f({
    blob: {
      maxFileSize: "32MB",
      maxFileCount: 1,
    },
  })
    .middleware(() => ({ uploadedBy: "user" }))
    .onUploadComplete(({ file }) => {
      console.log("Upload complete for:", file.name, "url:", file.ufsUrl);
      return { url: file.ufsUrl };
    }),
} satisfies FileRouter;

export type OurFileRouter = typeof ourFileRouter;