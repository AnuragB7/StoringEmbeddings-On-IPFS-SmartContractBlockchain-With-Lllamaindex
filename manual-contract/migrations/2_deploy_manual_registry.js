const ManualRegistry = artifacts.require("ManualRegistry");

module.exports = function(deployer) {
  deployer.deploy(ManualRegistry);
};