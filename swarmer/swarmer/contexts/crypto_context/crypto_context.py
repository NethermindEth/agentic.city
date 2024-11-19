from typing import Optional, Dict
import os
import json
from pathlib import Path
from uuid import uuid4
import secrets
from eth_account import Account
from eth_typing import Address
from web3 import Web3
from swarmer.tools.utils import tool
from swarmer.swarmer_types import AgentIdentity, Context, Tool

# Token address mapping
TOKEN_ADDRESSES = {
    "eth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
    "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "dai": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    # Add more tokens as needed
}

class CryptoContext(Context):
    """Context for crypto operations including key management and DeFi interactions."""
    
    tools: list[Tool] = []

    def __init__(self) -> None:
        self.tools.extend([
            self.get_balance,
            self.request_faucet
        ])
        self.id = str(uuid4())
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC_URL")))
        
        self.keys_dir = Path(os.getenv("KEYS_DIRECTORY", "secure/keys"))
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.private_keys: Dict[str, str] = {}

        # Setup faucet
        self.faucet_key_path = Path(os.getenv("KEYS_DIRECTORY", "secure/keys")) / "app.key"
        if not self.faucet_key_path.exists():
            self._generate_faucet_key()
        self._load_faucet_key()

    def _get_key_path(self, agent_id: str) -> Path:
        """Get the path to an agent's key file."""
        return self.keys_dir / f"{agent_id}.key"

    def _generate_key(self, agent_id: str) -> None:
        """Generate and securely store a new private key for an agent."""
        private_key = secrets.token_hex(32)
        key_path = self._get_key_path(agent_id)
        
        # Store key with restricted permissions
        with open(key_path, 'w') as f:
            f.write(private_key)
        os.chmod(key_path, 0o600)
        
        self.private_keys[agent_id] = private_key

    def _load_key(self, agent_id: str) -> None:
        """Load an existing private key for an agent."""
        key_path = self._get_key_path(agent_id)
        if not key_path.exists():
            self._generate_key(agent_id)
            return
            
        with open(key_path, 'r') as f:
            private_key = f.read().strip()
        self.private_keys[agent_id] = private_key

    def _generate_faucet_key(self) -> None:
        """Generate and store the faucet's private key."""
        private_key = secrets.token_hex(32)
        
        # Store key with restricted permissions
        with open(self.faucet_key_path, 'w') as f:
            f.write(private_key)
        os.chmod(self.faucet_key_path, 0o600)

    def _load_faucet_key(self) -> None:
        """Load the faucet's private key."""
        with open(self.faucet_key_path, 'r') as f:
            self.faucet_key = f.read().strip()
        self.faucet_account = Account.from_key(self.faucet_key)
        self.faucet_address = self.faucet_account.address

    def get_context_instructions(self, agent: AgentIdentity) -> Optional[str]:
        # Load key if not already loaded
        if agent.id not in self.private_keys:
            self._load_key(agent.id)
        
        # Get public address
        account = Account.from_key(self.private_keys[agent.id])
        
        return f"""
        You have access to crypto trading capabilities through:
        1. Token swaps on Uniswap
        2. Balance checking
        3. Price checking
        
        Your Ethereum address is: {account.address}
        
        In your first message to any user, you should:
        1. Mention that you have a dedicated Ethereum wallet
        2. Share your address: {account.address}
        3. Politely ask them to send some ETH to enable trading capabilities
        4. Explain that you'll need ETH for gas fees and tokens for trading
        
        Use simple token symbols like 'eth', 'usdc', 'dai'.
        All operations are performed on mainnet.
        
        When discussing transactions or balances, always reference your Ethereum address.
        Before attempting any trades, check your balance to ensure you have sufficient funds.
        """

    def get_context(self, agent: AgentIdentity) -> Optional[str]:
        if agent.id not in self.private_keys:
            self._load_key(agent.id)
        account = Account.from_key(self.private_keys[agent.id])
        return f"Ethereum address: {account.address}"

    # Todo: Add swap function

    @tool
    def get_balance(
        self,
        agent_identity: AgentIdentity,
        token: str = "eth"
    ) -> str:
        """Get token balance for the agent's address."""
        try:
            account = Account.from_key(self.private_keys[agent_identity.id])
            if token.lower() == "eth":
                balance = self.w3.eth.get_balance(account.address)
                return f"ETH Balance: {self.w3.from_wei(balance, 'ether')} ETH"
            
            token_address = TOKEN_ADDRESSES[token.lower()]
            # Define ERC20 ABI as a string to ensure correct typing
            erc20_abi = [{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }]
            
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            balance = token_contract.functions.balanceOf(account.address).call()
            return f"{token.upper()} Balance: {balance / 10**18} {token.upper()}"
            
        except Exception as e:
            return f"Failed to get balance: {str(e)}"

    # Todo: implement token price fetch

    @tool
    def request_faucet(
        self,
        agent_identity: AgentIdentity,
        amount: float = 0.1  # Default to 0.1 ETH
    ) -> str:
        """Request ETH from the faucet.
        
        Args:
            agent_identity: The agent requesting funds
            amount: Amount of ETH to request (max 0.1)
            
        Returns:
            Transaction result
        """
        try:
            # Load recipient's address
            if agent_identity.id not in self.private_keys:
                self._load_key(agent_identity.id)
            recipient = Account.from_key(self.private_keys[agent_identity.id])
            
            # Check faucet balance
            faucet_balance = self.w3.eth.get_balance(self.faucet_address)
            if faucet_balance < self.w3.to_wei(amount, 'ether'):
                return "Faucet has insufficient funds"
            
            # Limit amount to 0.1 ETH
            if amount > 0.1:
                amount = 0.1
                
            # Build transaction
            tx = {
                'nonce': self.w3.eth.get_transaction_count(self.faucet_address),
                'to': recipient.address,
                'value': self.w3.to_wei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            }
            
            # Sign and send
            signed_tx = self.faucet_account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            return f"Faucet sent {amount} ETH. Transaction: {self.w3.to_hex(tx_hash)}"
            
        except Exception as e:
            return f"Faucet request failed: {str(e)}"

    def serialize(self) -> dict:
        """Serialize context state - excluding private keys."""
        return {
            "id": self.id
        }

    def deserialize(self, state: dict, agent_identity: AgentIdentity) -> None:
        """Load state and restore private key access."""
        self.id = state["id"]
        self._load_key(agent_identity.id)