## 👩🏻‍🔬 Blockchain Data Science

This repository contains notebooks with my research for on-chain data on Ethereum, leveraging several APIs and libraries, including:

* [Etherscan API](https://docs.etherscan.io/api-endpoints/accounts)
* [The Graph with Uniswap subgraph GraphQL API](https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3)
* [Python web3.py library](https://web3py.readthedocs.io/en/stable/)



### Notebooks

* [Extracting on-data from a list of Ethereum public addresses](https://github.com/aquario-crypto/Blockchain-Data-Science/tree/main/on-chain-data-by-address):
    * Given a list of public addresses, extract the current token balance, and parse the transaction history for token transfers/swaps.

* [Leveraging Uniswap subgraph to extract token pair information](https://github.com/aquario-crypto/Blockchain-Data-Science/tree/main/uniswap-data):
    * Use The Graph Explorer to access the Uniswap subgraph and analyze the UNI and WETH token pair data. 

* [Retrieving DAO tokens and pools data](https://github.com/aquario-crypto/Blockchain-Data-Science/tree/main/dao-data):
    * Use The Graph Explorer to access the Uniswap subgraph and analyze the data related to a list of DAO tokens.



Installation and setup instructions are available in the directories above.
