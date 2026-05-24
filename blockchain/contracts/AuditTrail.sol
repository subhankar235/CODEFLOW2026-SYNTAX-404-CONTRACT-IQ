// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title AuditTrail
 * @dev Append-only, cryptographically chained audit log for legal contract lifecycle events.
 *      Each event stores a hash of the previous event forming a tamper-evident linked list.
 */
contract AuditTrail {
    // ─── Enums ───────────────────────────────────────────────────────────────
    enum EventType {
        UPLOADED,       // 0 — contract file uploaded to platform
        ANALYZED,       // 1 — AI risk analysis completed
        SIGNED,         // 2 — user wallet-signed the document
        COUNTER_OFFERED,// 3 — counter-offer generated
        EXPORTED        // 4 — PDF report exported / shared
    }

    // ─── Structs ────────────────────────────────────────────────────────────
    struct AuditEvent {
        bytes32   contractHash;      // keccak256(pdfBytes) — links to ContractRegistry
        EventType eventType;
        address   actorAddress;      // wallet that triggered the event
        bytes32   dataHash;          // keccak256(eventPayloadJson)
        bytes32   previousEventHash; // hash of prior AuditEvent for this contract (0x0 if first)
        uint256   timestamp;         // block.timestamp
    }

    // ─── State ───────────────────────────────────────────────────────────────
    address public owner;

    // contractHash → ordered list of event IDs
    mapping(bytes32 => uint256[]) private _contractEventIds;

    // global event store
    AuditEvent[] private _events;

    // contractHash → hash of the last logged event (for chaining)
    mapping(bytes32 => bytes32) private _lastEventHash;

    // ─── Events ──────────────────────────────────────────────────────────────
    event AuditEventLogged(
        uint256 indexed eventId,
        bytes32 indexed contractHash,
        EventType indexed eventType,
        address actorAddress,
        uint256 timestamp
    );

    // ─── Errors ──────────────────────────────────────────────────────────────
    error Unauthorized();
    error EmptyHash();
    error InvalidEventType(uint8 eventType);

    // ─── Modifier ────────────────────────────────────────────────────────────
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    // ─── Constructor ─────────────────────────────────────────────────────────
    constructor() {
        owner = msg.sender;
    }

    // ─── External Functions ──────────────────────────────────────────────────

    /**
     * @notice Log an audit event for a contract.
     * @param contractHash  keccak256(pdfBytes) — must already be in ContractRegistry
     * @param eventType     One of the EventType enum values (0–4)
     * @param actorAddress  The wallet address performing the action
     * @param dataHash      keccak256(JSON payload describing the event)
     * @return eventId      The index of the newly created event
     */
    function logEvent(
        bytes32 contractHash,
        uint8   eventType,
        address actorAddress,
        bytes32 dataHash
    ) external returns (uint256 eventId) {
        if (contractHash == bytes32(0)) revert EmptyHash();
        if (dataHash == bytes32(0))     revert EmptyHash();
        if (eventType > uint8(EventType.EXPORTED)) revert InvalidEventType(eventType);

        bytes32 prevHash = _lastEventHash[contractHash];

        AuditEvent memory evt = AuditEvent({
            contractHash:      contractHash,
            eventType:         EventType(eventType),
            actorAddress:      actorAddress,
            dataHash:          dataHash,
            previousEventHash: prevHash,
            timestamp:         block.timestamp
        });

        eventId = _events.length;
        _events.push(evt);
        _contractEventIds[contractHash].push(eventId);

        // Update the chain tip: hash of this event's key fields becomes next prevHash
        _lastEventHash[contractHash] = keccak256(
            abi.encodePacked(contractHash, eventType, actorAddress, dataHash, block.timestamp, eventId)
        );

        emit AuditEventLogged(eventId, contractHash, EventType(eventType), actorAddress, block.timestamp);
        return eventId;
    }

    /**
     * @notice Return all event IDs recorded for a contract.
     */
    function getEventIds(bytes32 contractHash)
        external
        view
        returns (uint256[] memory)
    {
        return _contractEventIds[contractHash];
    }

    /**
     * @notice Return a single audit event by its global ID.
     */
    function getEvent(uint256 eventId)
        external
        view
        returns (AuditEvent memory)
    {
        require(eventId < _events.length, "AuditTrail: event does not exist");
        return _events[eventId];
    }

    /**
     * @notice Return all events for a given contract hash in order.
     */
    function getEvents(bytes32 contractHash)
        external
        view
        returns (AuditEvent[] memory)
    {
        uint256[] memory ids = _contractEventIds[contractHash];
        AuditEvent[] memory result = new AuditEvent[](ids.length);
        for (uint256 i = 0; i < ids.length; i++) {
            result[i] = _events[ids[i]];
        }
        return result;
    }

    /**
     * @notice Return the current chain-tip hash for a contract (used for tamper detection).
     */
    function getLastEventHash(bytes32 contractHash) external view returns (bytes32) {
        return _lastEventHash[contractHash];
    }

    /**
     * @notice Return total number of events globally.
     */
    function totalEvents() external view returns (uint256) {
        return _events.length;
    }

    /**
     * @notice Transfer ownership.
     */
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert Unauthorized();
        owner = newOwner;
    }
}
