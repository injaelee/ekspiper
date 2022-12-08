from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.wallet.main import Wallet
from xrpl.models.amounts.issued_currency_amount import IssuedCurrencyAmount
from xrpl.models.requests.book_offers import BookOffers
from xrpl.asyncio.clients.utils import request_to_json_rpc
from xrpl.models.requests import AMMInfo, SubmitOnly
from xrpl.models.transactions import (
    OfferCreate, AMMDeposit, AMMVote, AMMBid, AMMCreate
)
from xrpl.models.amounts import Amount
from xrpl.models.currencies import XRP, IssuedCurrency
import xrpl
from collections import namedtuple
from typing import Dict, Union, Set
import json
import logging
import sys


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------------------------- #
#                                                                                                   #
# ------------------------------------------------------------------------------------------------- #

WalletSecret = namedtuple("WalletSecret", ["seed", "sequence"])

class WalletBuilder:
    def __init__(self):
        self.wallet_secret: WalletSecret = None
        self.xrpl_client = None

    def with_wallet_secret(self,
        wallet_secret: WalletSecret,
    ):
        self.wallet_secret = wallet_secret
        return self

    def with_xrpl_client(self,
        xrpl_client: JsonRpcClient,
    ):
        self.xrpl_client = xrpl_client
        return self

    def build(self) -> xrpl.wallet.main.Wallet:
        if self.wallet_secret:
            return xrpl.wallet.main.Wallet(
                seed = self.wallet_secret.seed,
                sequence = self.wallet_secret.sequence,
            )

        if not self.xrpl_client:
            raise RuntimeError("Missing XRPL Client to build a new wallet.")

        return generate_faucet_wallet(self.xrpl_client, debug=True)


"""

Build the wallet through the faucet

"""
def create_new_wallet(
    xrpl_client: JsonRpcClient,
):
    wallet_builder = WalletBuilder()
    the_wallet = wallet_builder.with_xrpl_client(
        xrpl_client).build()
    print("----------------------------")
    print(f"seed: {the_wallet.seed}")
    print(f"seq : {the_wallet.sequence}")

def existing_wallet(
    xrpl_client: JsonRpcClient,
    wallet_secret: WalletSecret,
):
    wallet_builder = WalletBuilder()
    wallet = wallet_builder.with_xrpl_client(
        xrpl_client,
    ).with_wallet_secret(
        wallet_secret,
    ).build()
    print("----------------------------")
    print(f"seed: {wallet.seed}")
    print(f"seq : {wallet.sequence}")
    return wallet

# ------------------------------------------------------------------------------------------------- #
#                                                                                                   #
# ------------------------------------------------------------------------------------------------- #


"""


{"method": "amm_info","params": [{"amm_id": "91528CE8BD8126BACE1B9797E4BD55CFCAB7B58F9A19BE04EF13E5205B793B92"}]}


"""


# ------------------------------------------------------------------------------------------------- #
#                                                                                                   #
# ------------------------------------------------------------------------------------------------- #

def create_amm(
    xrpl_client: JsonRpcClient,
    creator_wallet: Wallet,
    asset_amount_1: IssuedCurrencyAmount,
    asset_amount_2: IssuedCurrencyAmount,
    trading_fee: int,
):
    amm_create_tx = AMMCreate(
        account = creator_wallet.classic_address,
        amount = asset_amount_1,
        amount2 = asset_amount_2,
        trading_fee = trading_fee,
    )
    signed_and_prepared_amm_create_tx = xrpl.transaction.safe_sign_and_autofill_transaction(
        transaction = amm_create_tx,
        wallet = creator_wallet,
        client = xrpl_client,
    )

    logging.debug(json.dumps(signed_and_prepared_amm_create_tx.to_xrpl(), indent = 2))

    response = xrpl.transaction.send_reliable_submission(
        signed_and_prepared_amm_create_tx,
        xrpl_client,
    )
    logger.info(json.dumps(response.result, indent = 2))

    # Note: the response does not contain the AMM ID so must query the AMM INFO with the asset pairs


def get_amm_info(
    xrpl_client: JsonRpcClient,
    asset_1: IssuedCurrency = None,
    asset_2: IssuedCurrency = None,
):
    logger.info("[get_amm_info] fetching by asset")
    amm_info_req = AMMInfo(
        asset = asset_1,
        asset2 = asset_2,
    )

    import pdb; pdb.set_trace()

    response = xrpl_client.request(amm_info_req)

    return response.result

# ------------------------------------------------------------------------------------------------- #
#                                                                                                   #
# ------------------------------------------------------------------------------------------------- #

"""
# Setup an Existing Account

Modify the attributes of the account that will be the issuer of the token.

Pay attention to the 'TransferRate' which is a fee to charge
whenever counterparties transfer the currency you issue.

- Link: https://xrpl.org/accountset.html#transferrate

If you want charge a usage fee, make sure this is a non-zero postive number.


**TickSize**:
- Transaction processing engine calculates the exchange rate and truncates it based on `TickSize`
- 3 to 15 inclusive, or 0 to disable.
- exchange rates of those offers is rounded to the specified number of significant digits
  - This is not decimal places. ie) NN.XX has 4 significant digits and 2 decimal places

> For a default OfferCreate transaction (a "buy" Offer), the TakerPays amount
(the amount being bought) gets rounded. If the tfSell flag is enabled
(a "sell" Offer) the TakerGets amount (the amount being sold) gets rounded.

"""
def edit_issuer_account_set(
    xrpl_client: JsonRpcClient,
    issuer_wallet: Wallet,
    domain_name: str = "www.injaelee.com",
    transfer_rate: int = 0,
    tick_size: int = 5,
):
    logger.info(
        "[edit_account_set] setting transfer rate:[%d], tick_size:[%d], and domain:[%s].",
        transfer_rate,
        tick_size,
        domain_name,
    )
    issuer_account_mutate_tx = xrpl.models.transactions.AccountSet(
        account = issuer_wallet.classic_address,
        transfer_rate = transfer_rate,
        tick_size = tick_size,
        domain = bytes.hex(domain_name.encode("ASCII")),
        set_flag = xrpl.models.transactions.AccountSetFlag.ASF_DEFAULT_RIPPLE, # enabled rippling by default
    )

    signed_and_prepared_issuer_account_mutate_tx = xrpl.transaction.safe_sign_and_autofill_transaction(
        transaction = issuer_account_mutate_tx,
        wallet = issuer_wallet,
        client = xrpl_client,
    )

    logging.debug(json.dumps(signed_and_prepared_issuer_account_mutate_tx.to_xrpl(), indent = 2))
    # transaction_blob = encode(transaction.to_xrpl())
    # response = await client.request_impl(SubmitOnly(tx_blob=transaction_blob))
    # request_to_json_rpc(signed_and_prepared_issuer_account_mutate_tx)

    response = xrpl.transaction.send_reliable_submission(
        signed_and_prepared_issuer_account_mutate_tx,
        xrpl_client,
    )
    logger.info(json.dumps(response.result, indent = 2))


"""
# Auction Slot

The revenue from a successful AMMBid transaction is split between the current slot-holder and the pool.
We propose to always refund the current slot-holder of the remaining value of the slot computed from
the price at which they bought the slot.

24 hour timer starts with every successful bid

"""
def make_amm_bid(
    wallet,
):
    amm_bid_tx = AMMBid(
        account = wallet.classic_address,
        amm_id = "315270F394A77523466F86DB1E92F7620FC885FC355129A01AE4806F80DFE264",

        min_slot_price=IssuedCurrencyAmount(
            currency=LPToken_currency,
            issuer=LPToken_issuer,
            value="25",
        ),
        max_slot_price=IssuedCurrencyAmount(
            currency=LPToken_currency,
            issuer=LPToken_issuer,
            value="35",
        ),
        auth_accounts = auth_accounts,
        last_ledger_sequence=current_validated_ledger + 20,
        sequence = wallet.sequence,
        fee = "10",
    )
    amm_bid_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        transaction = amm_bid_tx,
        wallet = wallet,
        client = xrpl_client,
    )
    #response = xrpl.transaction.send_reliable_submission(
    #    amm_vote_prepared,
    #    xrpl_client,
    #)

def setup_trustlines_with(
    xrpl_client: JsonRpcClient,
    issuer_wallet: Wallet,
    distributor_wallet: Wallet,
    limit_amount: IssuedCurrencyAmount,
):
    logger.info(
        "[setup_trustlines_with] Setting up trustlines for asset '%s' with issuer %s.",
        limit_amount.currency,
        limit_amount.issuer,
    )
    trust_set_tx = xrpl.models.transactions.TrustSet(
        account = distributor_wallet.classic_address,
        limit_amount = limit_amount,
    )
    ts_tx_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        transaction = trust_set_tx,
        wallet = distributor_wallet,
        client = xrpl_client,
    )

    logging.debug(json.dumps(ts_tx_prepared.to_xrpl(), indent = 2))
    logger.info(
        "[setup_trustlines_with] Setting up trustline from distributor '%s' to issuer '%s",
        distributor_wallet.classic_address,
        issuer_wallet.classic_address,
    )
    response = xrpl.transaction.send_reliable_submission(
        ts_tx_prepared,
        xrpl_client,
    )
    logger.info(json.dumps(response.result, indent = 2))


def create_token(
    xrpl_client: JsonRpcClient,
    issuer_wallet: Wallet,
    distributor_wallet: Wallet,
    token_name: str,
    token_amount: int,
):
    logger.info(
        "[create_token] Creating asset '%s' with issuer %s.",
        token_name,
        issuer_wallet.classic_address,
    )
    trust_set_tx = xrpl.models.transactions.TrustSet(
        account = distributor_wallet.classic_address,
        limit_amount = IssuedCurrencyAmount(
            currency = token_name,
            issuer = issuer_wallet.classic_address,
            value = token_amount, # Large limit, arbitrarily chosen
        )
    )
    ts_tx_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        transaction = trust_set_tx,
        wallet = distributor_wallet,
        client = xrpl_client,
    )

    logging.debug(json.dumps(ts_tx_prepared.to_xrpl(), indent = 2))
    logger.info(
        "[create_token] Setting up trustline from distributor '%s' to issuer '%s",
        distributor_wallet.classic_address,
        issuer_wallet.classic_address,
    )
    response = xrpl.transaction.send_reliable_submission(
        ts_tx_prepared,
        xrpl_client,
    )
    logger.info(json.dumps(response.result, indent = 2))


    logger.info(
        "[create_token] Send '%d' of token '%s' to distributor '%s' from issuer '%s",
        token_amount,
        token_name,
        distributor_wallet.classic_address,
        issuer_wallet.classic_address,
    )
    send_token_tx = xrpl.models.transactions.Payment(
        account = issuer_wallet.classic_address,
        destination = distributor_wallet.classic_address,
        amount = IssuedCurrencyAmount(
            currency = token_name,
            issuer = issuer_wallet.classic_address,
            value = token_amount
        )
    )
    pay_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        transaction = send_token_tx,
        wallet = issuer_wallet,
        client = xrpl_client,
    )
    response = xrpl.transaction.send_reliable_submission(
        pay_prepared,
        xrpl_client,
    )
    logger.info(json.dumps(response.result, indent = 2))


def send_asset(
    xrpl_client: JsonRpcClient,
    source_wallet: Wallet,
    target_wallet: Wallet,
    asset_amount: IssuedCurrencyAmount,
):
    send_token_tx = xrpl.models.transactions.Payment(
        account = source_wallet.classic_address,
        destination = target_wallet.classic_address,
        amount = asset_amount,
    )
    pay_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        transaction = send_token_tx,
        wallet = source_wallet,
        client = xrpl_client,
    )
    logging.debug(json.dumps(pay_prepared.to_xrpl(), indent = 2))

    logger.info(
        "[send_asset] Send '%s' of token '%s : %s' to target '%s' from source '%s",
        asset_amount.value,
        asset_amount.issuer,
        asset_amount.currency,
        target_wallet.classic_address,
        source_wallet.classic_address
    )
    response = xrpl.transaction.send_reliable_submission(
        pay_prepared,
        xrpl_client,
    )
    logger.info(json.dumps(response.result, indent = 2))


def asset_amount_desc(
    asset_alias: str,
    asset_amount: Dict,
):
    return "{}[{}:{} - qty:{}]".format(
        asset_alias,
        asset_amount.get("currency", "N/A"),
        asset_amount.get("issuer", "N/A"),
        asset_amount.get("value", "0.00"),
    )


class AMMDepositExecutor:
    def __init__(self,
        amm_id: str,
        source_wallet: Wallet,
    ):
        self.target_amm_id = amm_id
        self.source_wallet = source_wallet

        self.asset_amounts: Set[Amount] = set()
        self.desired_lp_amount: Amount = None
        self.limit_price: int = None

    def _clear(self):
        self.asset_amounts: Set[Amount] = set()
        self.desired_lp_amount: Amount = None
        self.limit_price: int = None

    def with_deposit_asset(self,
        asset_amount: Amount,
    ):
        if len(self.asset_amounts) >= 2:
            raise ValueError("can deposit upto two types of assets")

        self.asset_amounts.add(asset_amount)
        return self

    def with_limit_price(self,
        limit_spot_price: int,
    ):
        self.limit_price = limit_spot_price
        return self

    def with_desired_lp_tokens(self,
        lp_token_amount: Amount,
    ):
        self.desired_lp_amount = lp_token_amount
        return self

    def _capture_amm_state(self,
        xrpl_client: JsonRpcClient,
        prefix: str,
    ):
        amm_info = get_amm_info(
            xrpl_client,
            amm_id = self.target_amm_id,
        )
        asset_a_amt = amm_info.get("Asset1")
        asset_b_amt = amm_info.get("Asset2")
        lp_token_amt = amm_info.get("LPToken")

        logger.info(
            "[make_deposit] {} {} and {} + {}".format(
                prefix,
                asset_amount_desc("A", asset_a_amt),
                asset_amount_desc("B", asset_b_amt),
                asset_amount_desc("LPToken", lp_token_amt),
        ))

        return amm_info

    def _print_amm_state_diff(self,
        start_state: Dict[str, str],
        end_state: Dict[str, str],
    ):
        start_a_amt = start_state.get("Asset1")
        start_b_amt = start_state.get("Asset2")
        start_lp_amt = start_state.get("LPToken")

        end_a_amt = end_state.get("Asset1")
        end_b_amt = end_state.get("Asset2")
        end_lp_amt = end_state.get("LPToken")

        diff_a = float(end_a_amt.get("value", 0.)) - float(start_a_amt.get("value", 0.))
        diff_b = float(end_b_amt.get("value", 0.)) - float(start_b_amt.get("value", 0.))
        diff_lp = float(end_lp_amt.get("value", 0.)) - float(start_lp_amt.get("value", 0.))

        logger.info("----------------------------")
        logger.info(
            "[make_deposit] Before: Asset1 {}".format(
                asset_amount_desc("A", start_a_amt),
        ))
        logger.info(
            "[make_deposit] After : Asset1 {}".format(
                asset_amount_desc("A", end_a_amt),
        ))
        logger.info(
            "[make_deposit] Result: DIFF {}".format(
                diff_a,
        ))
        logger.info("----------------------------")
        logger.info(
            "[make_deposit] Before: Asset2 {}".format(
                asset_amount_desc("B", start_b_amt),
        ))
        logger.info(
            "[make_deposit] After : Asset2 {}".format(
                asset_amount_desc("B", end_b_amt),
        ))
        logger.info(
            "[make_deposit] Result: DIFF {}".format(
                diff_b,
        ))
        logger.info("----------------------------")
        logger.info(
            "[make_deposit] Before: LPToken {}".format(
                asset_amount_desc("LPToken", start_lp_amt),
        ))
        logger.info(
            "[make_deposit] After : LPToken {}".format(
                asset_amount_desc("LPToken", end_lp_amt),
        ))
        logger.info(
            "[make_deposit] Result: DIFF {}".format(
                diff_lp,
        ))
        logger.info("----------------------------")

    def _build_deposit_txn(self) -> AMMDeposit:

        if len(self.asset_amounts) == 1:
            # captures 3 cases
            #  - asset amount + lp token
            #  - asset amount + e price
            #  - asset amount only
            return AMMDeposit(
                account = self.source_wallet.classic_address,
                amm_id = self.target_amm_id,
                asset1_in= list(self.asset_amounts)[0],
                lp_token = self.desired_lp_amount,
                e_price = self.limit_price,
            )

        if len(self.asset_amounts) == 2:
            return AMMDeposit(
                account = self.source_wallet.classic_address,
                amm_id = self.target_amm_id,
                asset1_in= list(self.asset_amounts)[0],
                asset2_in= list(self.asset_amounts)[1],
            )

        if self.desired_lp_amount:
            return AMMDeposit(
                account = self.source_wallet.classic_address,
                amm_id = self.target_amm_id,
                lp_token = self.desired_lp_amount,
            )

        raise ValueError("no option to build the 'AMMDeposit' transaction")


    def deposit(self,
        xrpl_client: JsonRpcClient,
        capture_amm_states: bool = True,
    ):
        starting_amm_state = self._capture_amm_state(xrpl_client, "starting with")

        asset_in_desc = ""
        for a_in in self.asset_amounts:
            if asset_in_desc:
                asset_in_desc += " + "
            asset_in_desc += asset_amount_desc("", a_in.to_dict())

        logger.info(
            "[make_deposit] Depositing to AMM ID[{}] with Assets[{}]".format(
            self.target_amm_id,
            asset_in_desc,
        ))

        amm_deposit_tx = self._build_deposit_txn()
        amm_deposit_tx_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
            transaction = amm_deposit_tx,
            wallet = self.source_wallet,
            client = xrpl_client,
        )
        response = xrpl.transaction.send_reliable_submission(
            amm_deposit_tx_prepared,
            xrpl_client,
        )
        logger.info(json.dumps(response.result, indent = 2))

        ending_amm_state = self._capture_amm_state(xrpl_client, "ends with")

        self._print_amm_state_diff(starting_amm_state, ending_amm_state)

        self._clear()


"""
{

  TransactionType: 'Payment',
  Account: 'rwZwTY69wUgtzPvPqh5cGSUNG9xg6eMxo2',
  Amount: {
    currency: 'LNQ',
    issuer: 'rn58GgimorQjTZBivRjyKKiBmThe9CZkXU',
    value: '50'
  },
  Destination: 'rwZwTY69wUgtzPvPqh5cGSUNG9xg6eMxo2',
  SendMax: {
    currency: 'RPL',
    issuer: 'rn58GgimorQjTZBivRjyKKiBmThe9CZkXU',
    value: '1000'
  }
}
"""
#class PaymentExecutor:




"""

# use the following cURL command to create a funded wallet/account
#
% curl -X POST https://ammfaucet.devnet.rippletest.net/accounts -s | python -mjson.tool


# a few accounts that were created and hard coded in this script
#
{ -- issuer
    "account": {
        "xAddress": "TV9REZpmFKhkhjrQcbV8ypaavw13TCh3rrzjsZEAApueju2",
        "secret": "ssZVUAd4kNvaZPgBf9ytSfvQH3em8",
        "classicAddress": "rNcKETj8YAx66AedXxmjuS41mNWWkgYjs3",
        "address": "rNcKETj8YAx66AedXxmjuS41mNWWkgYjs3"
    },
    "amount": 10000,
    "balance": 10000
}
{ -- distributor
    "account": {
        "address": "r3to76PunkAm3DJuNjhE1RZ48UVJ3EDb52",
        "classicAddress": "r3to76PunkAm3DJuNjhE1RZ48UVJ3EDb52",
        "secret": "sspsuieBpXAU92wE7J61RMoH96mns",
        "xAddress": "T7F8zzDbqDckAYHe68VJEjZMxrXRBvS1j6qZLogM3z7CPsF"
    },
    "amount": 10000,
    "balance": 10000
}
{ -- roaring
    "account": {
        "xAddress": "T7CEeBANZ5FGy5MBKyGKu2a8P8SCnSrzQHi4AMeC13GGir2",
        "secret": "sh5pRA72AjHUb5cXRaHH5P8vY7GWP",
        "classicAddress": "rnxzhsREjAG4s6yxLqhkcQXGxep5KYMSXR",
        "address": "rnxzhsREjAG4s6yxLqhkcQXGxep5KYMSXR"
    },
    "amount": 10000,
    "balance": 10000
}
{ -- kitty
    "account": {
        "xAddress": "TVPT8KEFRRiYWp4RjHSRNuqh2sog8gWXdCZ43brRSLAp19U",
        "secret": "shw3XnErVtiTzXpKP6kxse7dscbXV",
        "classicAddress": "rJvH4aJE55G3vNqJLoQkqGHZK6yQPLJEZh",
        "address": "rJvH4aJE55G3vNqJLoQkqGHZK6yQPLJEZh"
    },
    "amount": 10000,
    "balance": 10000
}

Templatized Functions


Create assets:
- Asset A
- Asset B
- Asset C
- Asset D

Create AMM's:
- A, B
- B, C
- C, D


Creating IOU's require
- Token Name
- Issuer Account
- Distributer Account


"""
def setup_stdout_logging():
    logging.basicConfig(
        stream = sys.stdout,  # set the out stream to STDOUT
        level = logging.DEBUG, # set level to INFO | logging.DEBUG
    )

if __name__ == "__main__":
    setup_stdout_logging()

    # https://s.altnet.rippletest.net:51234
    # http://amm.devnet.rippletest.net:51234
    # https://ammfaucet.devnet.rippletest.net
    # xrpl_url: str = "https://ammfaucet.devnet.rippletest.net"

    xrpl_url: str = "http://amm.devnet.rippletest.net:51234"
    xrpl_client = xrpl.clients.JsonRpcClient(xrpl_url)

    # create wallets if you need to
    # just uncomment
    # create_new_wallet(xrpl_client)

    import sys
    sys.exit()

    # create the token issuer aka. cold wallet
    issuer_wallet = existing_wallet(
        xrpl_client,
        WalletSecret("sEdSWKLe1PY6Pz4wVDk4YPBrN5aFnD9", 0),
    )

    # create the token distributor wallet that is going to
    # distribute/circulate the token to other accounts
    #
    distributor_wallet = existing_wallet(
        xrpl_client,
        WalletSecret("sspsuieBpXAU92wE7J61RMoH96mns", 0),
    )

    # just a user wallet from user 'roaring'
    #
    roaring_wallet = existing_wallet(
        xrpl_client,
        WalletSecret("sh5pRA72AjHUb5cXRaHH5P8vY7GWP", 0),
    )

    # just a user wallet from user 'kitty'
    #
    kitty_wallet = existing_wallet(
        xrpl_client,
        WalletSecret("shw3XnErVtiTzXpKP6kxse7dscbXV", 0),
    )

    # edit_issuer_account_set(xrpl_client, issuer_wallet)

    #create_token(
    #    xrpl_client,
    #    issuer_wallet,
    #    distributor_wallet,
    #    token_name = "CCC", <-- change this
    #    token_amount = 10000 <-- change this
    #)

    # So far created: AAA, BBB, CCC

    iou_AAA = IssuedCurrency(
        currency = "AAA",
        issuer = issuer_wallet.classic_address,
    )
    iou_BBB = IssuedCurrency(
        currency = "BBB",
        issuer = issuer_wallet.classic_address,
    )
    iou_CCC = IssuedCurrency(
        currency = "CCC",
        issuer = issuer_wallet.classic_address,
    )
    iou_TST = IssuedCurrency(
        currency = "TST",
        issuer = "rP9jPyP5kyvFRb6ZiRghAGw5u8SGAmU4bd",
    )

    #logger.info(XRP().to_amount(100))
    #logger.info(iou_AAA.to_amount(100))
    #logger.info(iou_BBB.to_amount(100))
    #logger.info(iou_CCC.to_amount(100))

    #setup_trustlines_with(
    #    xrpl_client = xrpl_client,
    #    issuer_wallet = issuer_wallet,
    #    distributor_wallet = roaring_wallet,
    #    limit_amount = iou_CCC.to_amount(1000000),
    #)
    #send_asset(
    #    xrpl_client = xrpl_client,
    #    source_wallet = distributor_wallet,
    #    target_wallet = roaring_wallet,
    #    asset_amount = iou_CCC.to_amount(350),
    #)
    # AMM(AAA,BBB): TXN 4DD8BC5044BDF2AEEDB5FF9DDBF225CE1E01DB16D6381F7C4A3B5A9868C8F301
    # AMM(BBB,CCC): TXN 91528CE8BD8126BACE1B9797E4BD55CFCAB7B58F9A19BE04EF13E5205B793B92 (rs3WkgPw6mMQJ54eZrnEbs5PC8qhJiMQNx0)

    # create the AMM(AAA,BBB) with 0 trading fees
    #create_amm(
    #    xrpl_client,
    #    creator_wallet = roaring_wallet,
    #    asset_amount_1 = iou_AAA.to_amount(150),
    #    asset_amount_2 = iou_CCC.to_amount(150),
    #    trading_fee = 0,
    #)

    """
    {"method": "amm_info","params": [{"amm_id": "rs3WkgPw6mMQJ54eZrnEbs5PC8qhJiMQNx"}]}
    {"method": "amm_info","params": [{"Asset1": {"currency": "CCC","issuer": "rNcKETj8YAx66AedXxmjuS41mNWWkgYjs3"},"Asset2": {"currency": "BBB","issuer": "rNcKETj8YAx66AedXxmjuS41mNWWkgYjs3"}}]}
    {"method": "amm_info","params": [{"asset1": {"currency": "0000000000000000000000004141410000000000","issuer": "95476D78B60B2B2130C6B395D62CD1E61603135F"},"asset2": {"currency": "0000000000000000000000004242420000000000","issuer": "95476D78B60B2B2130C6B395D62CD1E61603135F"}}]}


    curl -s -XPOST -d '' | python -mjson.tool

    curl -s -XPOST -d '{"method": "amm_info","params": [{"asset1": {"currency": "CCC","issuer": "rNcKETj8YAx66AedXxmjuS41mNWWkgYjs3"},"asset2": {"currency": "AAA","issuer": "rNcKETj8YAx66AedXxmjuS41mNWWkgYjs3"}}]}' http://amm.devnet.rippletest.net:51234 | python -mjson.tool
    """

    # send assets A to kitty_wallet
    #setup_trustlines_with(
    #    xrpl_client = xrpl_client,
    #    issuer_wallet = issuer_wallet,
    #    distributor_wallet = kitty_wallet,
    #    limit_amount = iou_AAA.to_amount(1000000),
    #)
    #send_asset(
    #    xrpl_client = xrpl_client,
    #    source_wallet = distributor_wallet,
    #    target_wallet = kitty_wallet,
    #    asset_amount = iou_AAA.to_amount(500),
    #)
    #get_amm_info(
    #    xrpl_client,
    #    asset_1 = iou_AAA.to_amount(0),
    #    asset_2 = iou_BBB.to_amount(0),
    #)
    amm_info = get_amm_info(
        xrpl_client,
        asset_1 = iou_TST.to_amount(0),
        asset_2 = XRP().to_amount(0),
    )
    print(json.dumps(amm_info, indent = 2))

    # AMM(AAA, BBB)
    # AMM ID: C85B7CD99C987D7A87F8F4F276F2A19DF0B026A932701D2D7FE375EAA6C3CBF0

    # AMM(AAA, CCC)
    # AMM ID: 5EEA6D855503F23C7FFBFDDD133CAF3733D80860452E37C0E2F1BEF6B0CE8F81

    # roaring has C and A
    amm_deposit_exec = AMMDepositExecutor(
        amm_id = "5EEA6D855503F23C7FFBFDDD133CAF3733D80860452E37C0E2F1BEF6B0CE8F81",
        source_wallet = kitty_wallet,
    )
    #amm_deposit_exec.with_deposit_asset(
    #    iou_CCC.to_amount(10),
    #).deposit(xrpl_client)

    #amm_deposit_exec.with_deposit_asset(
    #    iou_CCC.to_amount(5),
    #).with_deposit_asset(
    #    iou_AAA.to_amount(10),
    #).deposit(xrpl_client)

