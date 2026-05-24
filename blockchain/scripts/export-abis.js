/**
 * scripts/export-abis.js
 * After `npx hardhat compile`, run this to copy the ABI arrays from
 * Hardhat's artifacts into the clean blockchain/abis/ directory that
 * the Python backend reads at startup.
 */
const fs   = require("fs");
const path = require("path");

const CONTRACTS = ["ContractRegistry", "AuditTrail"];
const ARTIFACTS_BASE = path.join(__dirname, "..", "artifacts", "contracts");
const ABI_OUT        = path.join(__dirname, "..", "abis");

if (!fs.existsSync(ABI_OUT)) fs.mkdirSync(ABI_OUT, { recursive: true });

for (const name of CONTRACTS) {
  const artifactPath = path.join(ARTIFACTS_BASE, `${name}.sol`, `${name}.json`);
  if (!fs.existsSync(artifactPath)) {
    console.error(`[export-abis] Artifact not found: ${artifactPath}`);
    console.error(`              Run 'npx hardhat compile' first.`);
    process.exit(1);
  }
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  const outPath  = path.join(ABI_OUT, `${name}.json`);
  fs.writeFileSync(outPath, JSON.stringify(artifact.abi, null, 2));
  console.log(`[export-abis] ✓ ${name} ABI → ${outPath} (${artifact.abi.length} items)`);
}

console.log("[export-abis] Done.");
