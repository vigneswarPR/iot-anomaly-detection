// smart_contract/scripts/deploy.js
const hre = require("hardhat");

async function main() {
  const AnomalyLogger = await hre.ethers.getContractFactory("AnomalyLogger");
  const anomalyLogger = await AnomalyLogger.deploy();

  await anomalyLogger.waitForDeployment();

  console.log(
    `AnomalyLogger deployed to ${anomalyLogger.target}`
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});