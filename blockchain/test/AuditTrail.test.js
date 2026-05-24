const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AuditTrail", function () {
  let auditTrail;
  let owner;
  let actor1;
  let actor2;

  // EventType enum values (must match Solidity)
  const EventType = {
    UPLOADED: 0,
    ANALYZED: 1,
    SIGNED: 2,
    COUNTER_OFFERED: 3,
    EXPORTED: 4,
  };

  const samplePdfBytes = ethers.toUtf8Bytes("sample-contract-pdf-bytes");
  const samplePayload1 = ethers.toUtf8Bytes('{"action":"upload","filename":"contract.pdf"}');
  const samplePayload2 = ethers.toUtf8Bytes('{"action":"analyze","risk":"HIGH"}');

  const contractHash = ethers.keccak256(samplePdfBytes);
  const dataHash1 = ethers.keccak256(samplePayload1);
  const dataHash2 = ethers.keccak256(samplePayload2);

  beforeEach(async function () {
    [owner, actor1, actor2] = await ethers.getSigners();
    const AuditTrail = await ethers.getContractFactory("AuditTrail");
    auditTrail = await AuditTrail.deploy();
    await auditTrail.waitForDeployment();
  });

  // ── Deployment ────────────────────────────────────────────────────────────
  describe("Deployment", function () {
    it("Should set deployer as owner", async function () {
      expect(await auditTrail.owner()).to.equal(owner.address);
    });

    it("Should start with zero events", async function () {
      expect(await auditTrail.totalEvents()).to.equal(0n);
    });
  });

  // ── logEvent() ────────────────────────────────────────────────────────────
  describe("logEvent()", function () {
    it("Should log an event and emit AuditEventLogged", async function () {
      await expect(
        auditTrail.connect(actor1).logEvent(
          contractHash,
          EventType.UPLOADED,
          actor1.address,
          dataHash1
        )
      ).to.emit(auditTrail, "AuditEventLogged");
    });

    it("Should store correct event fields", async function () {
      await auditTrail.connect(actor1).logEvent(
        contractHash,
        EventType.UPLOADED,
        actor1.address,
        dataHash1
      );
      const evt = await auditTrail.getEvent(0);
      expect(evt.contractHash).to.equal(contractHash);
      expect(evt.eventType).to.equal(EventType.UPLOADED);
      expect(evt.actorAddress).to.equal(actor1.address);
      expect(evt.dataHash).to.equal(dataHash1);
      expect(evt.previousEventHash).to.equal(ethers.ZeroHash); // first event has no predecessor
      expect(evt.timestamp).to.be.gt(0n);
    });

    it("Should chain events: second event's previousEventHash is non-zero", async function () {
      await auditTrail.connect(actor1).logEvent(
        contractHash, EventType.UPLOADED, actor1.address, dataHash1
      );
      await auditTrail.connect(actor1).logEvent(
        contractHash, EventType.ANALYZED, actor1.address, dataHash2
      );

      const evt0 = await auditTrail.getEvent(0);
      const evt1 = await auditTrail.getEvent(1);

      // First event has zero previous hash
      expect(evt0.previousEventHash).to.equal(ethers.ZeroHash);
      // Second event must have a non-zero previous hash
      expect(evt1.previousEventHash).to.not.equal(ethers.ZeroHash);
    });

    it("Should increment totalEvents", async function () {
      await auditTrail.logEvent(contractHash, EventType.UPLOADED, actor1.address, dataHash1);
      await auditTrail.logEvent(contractHash, EventType.ANALYZED, actor1.address, dataHash2);
      expect(await auditTrail.totalEvents()).to.equal(2n);
    });

    it("Should revert with EmptyHash when contractHash is zero", async function () {
      await expect(
        auditTrail.logEvent(ethers.ZeroHash, EventType.UPLOADED, actor1.address, dataHash1)
      ).to.be.revertedWithCustomError(auditTrail, "EmptyHash");
    });

    it("Should revert with EmptyHash when dataHash is zero", async function () {
      await expect(
        auditTrail.logEvent(contractHash, EventType.UPLOADED, actor1.address, ethers.ZeroHash)
      ).to.be.revertedWithCustomError(auditTrail, "EmptyHash");
    });

    it("Should revert with InvalidEventType for out-of-range type", async function () {
      await expect(
        auditTrail.logEvent(contractHash, 99, actor1.address, dataHash1)
      ).to.be.revertedWithCustomError(auditTrail, "InvalidEventType");
    });

    it("Should support all 5 valid EventType values", async function () {
      for (const [, val] of Object.entries(EventType)) {
        const h = ethers.keccak256(ethers.toUtf8Bytes(`payload-${val}`));
        await expect(
          auditTrail.logEvent(contractHash, val, actor1.address, h)
        ).to.emit(auditTrail, "AuditEventLogged");
      }
    });
  });

  // ── getEventIds() ─────────────────────────────────────────────────────────
  describe("getEventIds()", function () {
    it("Should return empty array for contract with no events", async function () {
      const ids = await auditTrail.getEventIds(contractHash);
      expect(ids.length).to.equal(0);
    });

    it("Should return ordered event IDs for a contract", async function () {
      await auditTrail.logEvent(contractHash, EventType.UPLOADED, actor1.address, dataHash1);
      await auditTrail.logEvent(contractHash, EventType.ANALYZED, actor1.address, dataHash2);
      const ids = await auditTrail.getEventIds(contractHash);
      expect(ids.length).to.equal(2);
      expect(ids[0]).to.equal(0n);
      expect(ids[1]).to.equal(1n);
    });
  });

  // ── getEvents() ───────────────────────────────────────────────────────────
  describe("getEvents()", function () {
    it("Should return all events for a contract in order", async function () {
      await auditTrail.logEvent(contractHash, EventType.UPLOADED, actor1.address, dataHash1);
      await auditTrail.logEvent(contractHash, EventType.ANALYZED, actor2.address, dataHash2);

      const events = await auditTrail.getEvents(contractHash);
      expect(events.length).to.equal(2);
      expect(events[0].eventType).to.equal(BigInt(EventType.UPLOADED));
      expect(events[1].eventType).to.equal(BigInt(EventType.ANALYZED));
      expect(events[1].actorAddress).to.equal(actor2.address);
    });
  });

  // ── getLastEventHash() ────────────────────────────────────────────────────
  describe("getLastEventHash()", function () {
    it("Should return ZeroHash before any events", async function () {
      expect(await auditTrail.getLastEventHash(contractHash)).to.equal(ethers.ZeroHash);
    });

    it("Should return a non-zero hash after an event is logged", async function () {
      await auditTrail.logEvent(contractHash, EventType.UPLOADED, actor1.address, dataHash1);
      const lastHash = await auditTrail.getLastEventHash(contractHash);
      expect(lastHash).to.not.equal(ethers.ZeroHash);
    });

    it("Should change the chain tip after each new event", async function () {
      await auditTrail.logEvent(contractHash, EventType.UPLOADED, actor1.address, dataHash1);
      const hash1 = await auditTrail.getLastEventHash(contractHash);
      await auditTrail.logEvent(contractHash, EventType.ANALYZED, actor1.address, dataHash2);
      const hash2 = await auditTrail.getLastEventHash(contractHash);
      expect(hash1).to.not.equal(hash2);
    });
  });

  // ── Separate contracts don't share state ─────────────────────────────────
  describe("Isolation between contracts", function () {
    it("Events for different contract hashes are isolated", async function () {
      const contractHash2 = ethers.keccak256(ethers.toUtf8Bytes("different-pdf"));
      await auditTrail.logEvent(contractHash, EventType.UPLOADED, actor1.address, dataHash1);
      await auditTrail.logEvent(contractHash2, EventType.SIGNED, actor2.address, dataHash2);

      const events1 = await auditTrail.getEvents(contractHash);
      const events2 = await auditTrail.getEvents(contractHash2);
      expect(events1.length).to.equal(1);
      expect(events2.length).to.equal(1);
      expect(events1[0].eventType).to.equal(BigInt(EventType.UPLOADED));
      expect(events2[0].eventType).to.equal(BigInt(EventType.SIGNED));
    });
  });

  // ── transferOwnership() ──────────────────────────────────────────────────
  describe("transferOwnership()", function () {
    it("Should transfer ownership", async function () {
      await auditTrail.transferOwnership(actor1.address);
      expect(await auditTrail.owner()).to.equal(actor1.address);
    });

    it("Should revert when non-owner calls it", async function () {
      await expect(
        auditTrail.connect(actor1).transferOwnership(actor2.address)
      ).to.be.revertedWithCustomError(auditTrail, "Unauthorized");
    });
  });
});
