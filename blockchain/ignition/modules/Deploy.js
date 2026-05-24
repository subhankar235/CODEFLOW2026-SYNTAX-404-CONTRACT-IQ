const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

/**
 * Hardhat Ignition deployment module.
 * Deploys ContractRegistry and AuditTrail with deterministic addresses.
 * Run:
 *   npm run deploy:local    — Hardhat local node
 *   npm run deploy:amoy     — Polygon Amoy testnet
 *   npm run deploy:mainnet  — Polygon Mainnet
 */
const LegalTechBlockchainModule = buildModule("LegalTechBlockchainModule", (m) => {
  // ── Deploy ContractRegistry ───────────────────────────────────────────────
  const contractRegistry = m.contract("ContractRegistry", [], {
    id: "ContractRegistry",
  });

  // ── Deploy AuditTrail ─────────────────────────────────────────────────────
  const auditTrail = m.contract("AuditTrail", [], {
    id: "AuditTrail",
  });

  return { contractRegistry, auditTrail };
});

module.exports = LegalTechBlockchainModule;
