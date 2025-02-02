// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ManualRegistry {
    struct Manual {
        string contentCID;
        string embeddingsCID;
        uint256 version;
        address owner;
        bool isActive;
        mapping(address => bool) authorizedUsers;
    }
    
    mapping(string => Manual) public manuals;
    
    event ManualUploaded(string manualId, string contentCID, string embeddingsCID);
    event AccessGranted(string manualId, address user);
    
    function uploadManual(
        string memory manualId,
        string memory contentCID,
        string memory embeddingsCID,
        uint256 version
    ) public {
        Manual storage manual = manuals[manualId];
        manual.contentCID = contentCID;
        manual.embeddingsCID = embeddingsCID;
        manual.version = version;
        manual.owner = msg.sender;
        manual.isActive = true;
        manual.authorizedUsers[msg.sender] = true;
        
        emit ManualUploaded(manualId, contentCID, embeddingsCID);
    }
    
    function grantAccess(string memory manualId, address user) public {
        require(manuals[manualId].owner == msg.sender, "Not authorized");
        manuals[manualId].authorizedUsers[user] = true;
        emit AccessGranted(manualId, user);
    }
    
    function getManualCIDs(string memory manualId) public view returns (string memory, string memory) {
        require(manuals[manualId].authorizedUsers[msg.sender], "Not authorized");
        return (manuals[manualId].contentCID, manuals[manualId].embeddingsCID);
    }
}