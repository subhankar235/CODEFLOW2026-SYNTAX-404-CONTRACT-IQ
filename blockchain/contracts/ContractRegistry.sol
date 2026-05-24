// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ContractRegistry
 * @dev Stores immutable keccak256 hashes of legal contract PDFs and their metadata.
 *      Each registration is append-only and permanently verifiable on Polygon PoS.
 */
contract ContractRegistry {
    // ─── Structs ────────────────────────────────────────────────────────────
    struct ContractRecord {
        bytes32 contractHash;    // keccak256 of the PDF bytes
        bytes32 metadataHash;    // keccak256 of the JSON metadata string
        address uploaderAddress; // wallet that signed/registered
        uint256 timestamp;       // block.timestamp at registration
        string  ipfsCid;         // IPFS CID of the pinned document
        bool    exists;          // guard flag to distinguish zero-hash records
    }

    // ─── State ───────────────────────────────────────────────────────────────
    address public owner;
    mapping(bytes32 => ContractRecord) private _records;   // contractHash → record
    bytes32[] private _allHashes;                          // ordered registry

    // ─── Events ──────────────────────────────────────────────────────────────
    event ContractRegistered(
        bytes32 indexed contractHash,
        address indexed uploader,
        uint256 timestamp,
        string  ipfsCid
    );

    // ─── Errors ──────────────────────────────────────────────────────────────
    error AlreadyRegistered(bytes32 contractHash);
    error NotFound(bytes32 contractHash);
    error Unauthorized();
    error EmptyHash();
    error EmptyIpfsCid();

    // ─── Modifiers ───────────────────────────────────────────────────────────
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
     * @notice Register a new legal contract on-chain.
     * @param contractHash  keccak256(pdfBytes)
     * @param metadataHash  keccak256(jsonMetadataBytes)
     * @param ipfsCid       IPFS content identifier for the pinned PDF
     */
    function register(
        bytes32 contractHash,
        bytes32 metadataHash,
        string calldata ipfsCid
    ) external {
        if (contractHash == bytes32(0)) revert EmptyHash();
        if (bytes(ipfsCid).length == 0)  revert EmptyIpfsCid();
        if (_records[contractHash].exists) revert AlreadyRegistered(contractHash);

        _records[contractHash] = ContractRecord({
            contractHash:    contractHash,
            metadataHash:    metadataHash,
            uploaderAddress: msg.sender,
            timestamp:       block.timestamp,
            ipfsCid:         ipfsCid,
            exists:          true
        });
        _allHashes.push(contractHash);

        emit ContractRegistered(contractHash, msg.sender, block.timestamp, ipfsCid);
    }

    /**
     * @notice Retrieve a contract record by its hash.
     * @param contractHash  keccak256(pdfBytes)
     */
    function getContract(bytes32 contractHash)
        external
        view
        returns (ContractRecord memory)
    {
        if (!_records[contractHash].exists) revert NotFound(contractHash);
        return _records[contractHash];
    }

    /**
     * @notice Check whether a hash has been registered.
     */
    function isRegistered(bytes32 contractHash) external view returns (bool) {
        return _records[contractHash].exists;
    }

    /**
     * @notice Return the total number of registered contracts.
     */
    function registrySize() external view returns (uint256) {
        return _allHashes.length;
    }

    /**
     * @notice Return a page of registered hashes (pagination helper).
     * @param offset  Start index
     * @param limit   Number of items
     */
    function getHashesPaginated(uint256 offset, uint256 limit)
        external
        view
        returns (bytes32[] memory)
    {
        uint256 total = _allHashes.length;
        if (offset >= total) return new bytes32[](0);
        uint256 end = offset + limit;
        if (end > total) end = total;
        bytes32[] memory page = new bytes32[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            page[i - offset] = _allHashes[i];
        }
        return page;
    }

    /**
     * @notice Transfer ownership to a new address.
     */
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert Unauthorized();
        owner = newOwner;
    }
}
