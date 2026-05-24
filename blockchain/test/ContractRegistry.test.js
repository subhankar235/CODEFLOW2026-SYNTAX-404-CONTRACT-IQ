const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ContractRegistry", function () {
  let registry;
  let owner;
  let user1;
  let user2;

  // Sample test data
  const samplePdfBytes = ethers.toUtf8Bytes("fake-pdf-bytes-for-testing");
  const sampleMetaBytes = ethers.toUtf8Bytes('{"contract_id":"abc","sha256":"deadbeef"}');
  const sampleCid = "QmTestCIDabcdef1234567890";

  const contractHash = ethers.keccak256(samplePdfBytes);
  const metadataHash = ethers.keccak256(sampleMetaBytes);

  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();
    const ContractRegistry = await ethers.getContractFactory("ContractRegistry");
    registry = await ContractRegistry.deploy();
    await registry.waitForDeployment();
  });

  // ── Deployment ────────────────────────────────────────────────────────────
  describe("Deployment", function () {
    it("Should set the deployer as owner", async function () {
      expect(await registry.owner()).to.equal(owner.address);
    });

    it("Should start with zero registered contracts", async function () {
      expect(await registry.registrySize()).to.equal(0n);
    });
  });

  // ── register() ───────────────────────────────────────────────────────────
  describe("register()", function () {
    it("Should register a contract and emit ContractRegistered", async function () {
      await expect(
        registry.connect(user1).register(contractHash, metadataHash, sampleCid)
      )
        .to.emit(registry, "ContractRegistered")
        .withArgs(contractHash, user1.address, await getBlockTimestamp(), sampleCid);
    });

    it("Should store the correct record fields", async function () {
      const tx = await registry.connect(user1).register(contractHash, metadataHash, sampleCid);
      await tx.wait();

      const record = await registry.getContract(contractHash);
      expect(record.contractHash).to.equal(contractHash);
      expect(record.metadataHash).to.equal(metadataHash);
      expect(record.uploaderAddress).to.equal(user1.address);
      expect(record.ipfsCid).to.equal(sampleCid);
      expect(record.exists).to.equal(true);
      expect(record.timestamp).to.be.gt(0n);
    });

    it("Should increment registrySize after registration", async function () {
      await registry.connect(user1).register(contractHash, metadataHash, sampleCid);
      expect(await registry.registrySize()).to.equal(1n);
    });

    it("Should revert with AlreadyRegistered on duplicate hash", async function () {
      await registry.connect(user1).register(contractHash, metadataHash, sampleCid);
      await expect(
        registry.connect(user2).register(contractHash, metadataHash, sampleCid)
      ).to.be.revertedWithCustomError(registry, "AlreadyRegistered");
    });

    it("Should revert with EmptyHash when contractHash is zero", async function () {
      await expect(
        registry.connect(user1).register(ethers.ZeroHash, metadataHash, sampleCid)
      ).to.be.revertedWithCustomError(registry, "EmptyHash");
    });

    it("Should revert with EmptyIpfsCid when CID is empty string", async function () {
      await expect(
        registry.connect(user1).register(contractHash, metadataHash, "")
      ).to.be.revertedWithCustomError(registry, "EmptyIpfsCid");
    });

    it("Should allow different users to register different contracts", async function () {
      const hash2 = ethers.keccak256(ethers.toUtf8Bytes("another-pdf"));
      await registry.connect(user1).register(contractHash, metadataHash, sampleCid);
      await registry.connect(user2).register(hash2, metadataHash, "QmAnotherCID");
      expect(await registry.registrySize()).to.equal(2n);
    });
  });

  // ── getContract() ────────────────────────────────────────────────────────
  describe("getContract()", function () {
    it("Should revert with NotFound for unregistered hash", async function () {
      await expect(
        registry.getContract(contractHash)
      ).to.be.revertedWithCustomError(registry, "NotFound");
    });

    it("Should return correct record for registered hash", async function () {
      await registry.connect(user1).register(contractHash, metadataHash, sampleCid);
      const record = await registry.getContract(contractHash);
      expect(record.uploaderAddress).to.equal(user1.address);
    });
  });

  // ── isRegistered() ───────────────────────────────────────────────────────
  describe("isRegistered()", function () {
    it("Should return false for unregistered hash", async function () {
      expect(await registry.isRegistered(contractHash)).to.equal(false);
    });

    it("Should return true after registration", async function () {
      await registry.connect(user1).register(contractHash, metadataHash, sampleCid);
      expect(await registry.isRegistered(contractHash)).to.equal(true);
    });
  });

  // ── getHashesPaginated() ─────────────────────────────────────────────────
  describe("getHashesPaginated()", function () {
    it("Should return empty array when offset exceeds total", async function () {
      const result = await registry.getHashesPaginated(100n, 10n);
      expect(result.length).to.equal(0);
    });

    it("Should paginate correctly", async function () {
      // Register 3 contracts
      for (let i = 0; i < 3; i++) {
        const h = ethers.keccak256(ethers.toUtf8Bytes(`pdf-bytes-${i}`));
        await registry.register(h, metadataHash, `Qm${i}`);
      }
      const page1 = await registry.getHashesPaginated(0n, 2n);
      const page2 = await registry.getHashesPaginated(2n, 2n);
      expect(page1.length).to.equal(2);
      expect(page2.length).to.equal(1);
    });
  });

  // ── transferOwnership() ──────────────────────────────────────────────────
  describe("transferOwnership()", function () {
    it("Should transfer ownership to a new address", async function () {
      await registry.transferOwnership(user1.address);
      expect(await registry.owner()).to.equal(user1.address);
    });

    it("Should revert when called by non-owner", async function () {
      await expect(
        registry.connect(user1).transferOwnership(user2.address)
      ).to.be.revertedWithCustomError(registry, "Unauthorized");
    });

    it("Should revert when new owner is zero address", async function () {
      await expect(
        registry.transferOwnership(ethers.ZeroAddress)
      ).to.be.revertedWithCustomError(registry, "Unauthorized");
    });
  });

  // ── Helper ───────────────────────────────────────────────────────────────
  async function getBlockTimestamp() {
    const block = await ethers.provider.getBlock("latest");
    return block.timestamp;
  }
});
