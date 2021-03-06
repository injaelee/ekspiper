class XRPLTransactionSchema:
    SCHEMA = {
        "_ExecutionID": {str}, # to note custom export execution
        "Account": {str},
        "Amendment": {str},
        "Amount": {str, dict},
        "Amount.currency": {str},
        "Amount.issuer": {str},
        "Amount.value": {str},
        "Authorize": {str},
        "BaseFee": {str},
        "CancelAfter": {int},
        "Channel": {str},
        "CheckID": {str},
        "DeliverMin": {dict},
        "DeliverMin.currency": {str},
        "DeliverMin.issuer": {str},
        "DeliverMin.value": {str},
        "Destination": {str},
        "DestinationTag": {int},
        "Expiration": {int},
        "Fee": {str},
        "FinishAfter": {int},
        "Flags": {int},
        "LastLedgerSequence": {int},
        "LedgerSequence": {int},
        "LimitAmount": {dict},
        "LimitAmount.currency": {str},
        "LimitAmount.issuer": {str},
        "LimitAmount.value": {str},
        "Memos": {list},
        "Memos.Memo": {dict},
        "Memos.Memo.MemoData": {str},
        "Memos.Memo.MemoFormat": {str},
        "Memos.Memo.MemoType": {str},
        "OfferSequence": {int},
        "Owner": {str},
        "PublicKey": {str},
        "QualityIn": {int},
        "QualityOut": {int},
        "ReferenceFeeUnits": {int},
        "RegularKey": {str},
        "ReserveBase": {int},
        "ReserveIncrement": {int},
        "SendMax": {str, dict},
        "SendMax.currency": {str},
        "SendMax.issuer": {str},
        "SendMax.value": {str},
        "Sequence": {int},
        "SetFlag": {int},
        "SettleDelay": {int},
        "SignerEntries": {list},
        "SignerEntries.SignerEntry": {dict},
        "SignerEntries.SignerEntry.Account": {str},
        "SignerEntries.SignerEntry.SignerWeight": {int},
        "SignerQuorum": {int},
        "Signers": {list},
        "Signers.Signer": {dict},
        "Signers.Signer.Account": {str},
        "Signers.Signer.SigningPubKey": {str},
        "Signers.Signer.TxnSignature": {str},
        "SigningPubKey": {str},
        "SourceTag": {int},
        "TakerGets": {str, dict},
        "TakerGets.currency": {str},
        "TakerGets.issuer": {str},
        "TakerGets.value": {str},
        "TakerPays": {str, dict},
        "TakerPays.currency": {str},
        "TakerPays.issuer": {str},
        "TakerPays.value": {str},
        "TicketCount": {int},
        "TicketSequence": {int},
        "TransactionType": {str},
        "TxnSignature": {str},
        "UNLModifyDisabling": {int},
        "UNLModifyValidator": {str},
        "metaData": {dict},
        "metaData.AffectedNodes": {list},
        "metaData.AffectedNodes.CreatedNode": {dict},
        "metaData.AffectedNodes.CreatedNode.LedgerEntryType": {str},
        "metaData.AffectedNodes.CreatedNode.LedgerIndex": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields": {dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.Account": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.Amount": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.Balance": {str, dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.Balance.currency": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.Balance.issuer": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.Balance.value": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.BookDirectory": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.CancelAfter": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.Destination": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.DestinationTag": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.ExchangeRate": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.Expiration": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.FinishAfter": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.Flags": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.HighLimit": {dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.HighLimit.currency": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.HighLimit.issuer": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.HighLimit.value": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.HighNode": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.IndexPrevious": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.LowLimit": {dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.LowLimit.currency": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.LowLimit.issuer": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.LowLimit.value": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.LowNode": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.Owner": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.OwnerNode": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.PublicKey": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.RootIndex": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.SendMax": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.Sequence": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.SettleDelay": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.SignerEntries": {list},
        "metaData.AffectedNodes.CreatedNode.NewFields.SignerEntries.SignerEntry": {dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.SignerEntries.SignerEntry.Account": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.SignerEntries.SignerEntry.SignerWeight": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.SignerQuorum": {int},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerGets.currency": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerGets.issuer": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerGets.value": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerGetsCurrency": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerGetsIssuer": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerPays.currency": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerPays.issuer": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerPays.value": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerPaysCurrency": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerPaysIssuer": {str},
        "metaData.AffectedNodes.CreatedNode.NewFields.TicketSequence": {int},
        "metaData.AffectedNodes.DeletedNode": {dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields": {dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Account": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Amount": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Balance": {str, dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Balance.currency": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Balance.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Balance.value": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.BookDirectory": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.BookNode": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.CancelAfter": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Destination": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.DestinationNode": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.DestinationTag": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.ExchangeRate": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Expiration": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.FinishAfter": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Flags": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.HighLimit": {dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.HighLimit.currency": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.HighLimit.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.HighLimit.value": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.HighNode": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.IndexNext": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.IndexPrevious": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.LowLimit": {dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.LowLimit.currency": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.LowLimit.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.LowLimit.value": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.LowNode": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Owner": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.OwnerCount": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.OwnerNode": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.PreviousTxnID": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.PreviousTxnLgrSeq": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.PublicKey": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.RootIndex": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.SendMax": {dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.SendMax.currency": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.SendMax.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.SendMax.value": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Sequence": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.SettleDelay": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.SourceTag": {int},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerGets.currency": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerGets.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerGets.value": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerGetsCurrency": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerGetsIssuer": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerPays.currency": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerPays.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerPays.value": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerPaysCurrency": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerPaysIssuer": {str},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TicketSequence": {int},
        "metaData.AffectedNodes.DeletedNode.LedgerEntryType": {str},
        "metaData.AffectedNodes.DeletedNode.LedgerIndex": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields": {dict},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.Balance": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.Flags": {int},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.HighLimit": {dict},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.HighLimit.currency": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.HighLimit.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.HighLimit.value": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.LowLimit": {dict},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.LowLimit.currency": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.LowLimit.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.LowLimit.value": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.Sequence": {int},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerGets.currency": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerGets.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerGets.value": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerPays.currency": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerPays.issuer": {str},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerPays.value": {str},
        "metaData.AffectedNodes.ModifiedNode": {dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields": {dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Account": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.AccountTxnID": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Amendments": {list},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Balance": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Balance.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Balance.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Balance.value": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.BaseFee": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.BookDirectory": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.BookNode": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.DisabledValidators": {list},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.DisabledValidators.DisabledValidator": {dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.DisabledValidators.DisabledValidator.FirstLedgerSequence": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.DisabledValidators.DisabledValidator.PublicKey": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Domain": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.EmailHash": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.ExchangeRate": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Expiration": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Flags": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.HighLimit": {dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.HighLimit.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.HighLimit.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.HighLimit.value": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.HighNode": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.IndexNext": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.IndexPrevious": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.LowLimit": {dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.LowLimit.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.LowLimit.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.LowLimit.value": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.LowNode": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.MessageKey": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Owner": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.OwnerCount": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.OwnerNode": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.ReferenceFeeUnits": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.RegularKey": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.ReserveBase": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.ReserveIncrement": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.RootIndex": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Sequence": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerGets.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerGets.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerGets.value": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerGetsCurrency": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerGetsIssuer": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerPays.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerPays.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerPays.value": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerPaysCurrency": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerPaysIssuer": {str},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TicketCount": {int},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.ValidatorToReEnable": {str},
        "metaData.AffectedNodes.ModifiedNode.LedgerEntryType": {str},
        "metaData.AffectedNodes.ModifiedNode.LedgerIndex": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields": {dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Amendments": {list},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Balance": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Balance.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Balance.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Balance.value": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Flags": {int},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.IndexNext": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.IndexPrevious": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.LowLimit": {dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.LowLimit.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.LowLimit.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.LowLimit.value": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Majorities": {list},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Majorities.Majority": {dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Majorities.Majority.Amendment": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Majorities.Majority.CloseTime": {int},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.OwnerCount": {int},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.ReserveBase": {int},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.ReserveIncrement": {int},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Sequence": {int},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerGets.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerGets.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerGets.value": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerPays.currency": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerPays.issuer": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerPays.value": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TicketCount": {int},
        "metaData.AffectedNodes.ModifiedNode.PreviousTxnID": {str},
        "metaData.AffectedNodes.ModifiedNode.PreviousTxnLgrSeq": {int},
        "metaData.DeliveredAmount": {str, dict},
        "metaData.DeliveredAmount.currency": {str},
        "metaData.DeliveredAmount.issuer": {str},
        "metaData.DeliveredAmount.value": {str},
        "metaData.TransactionIndex": {int},
        "metaData.TransactionResult": {str},
        "metaData.delivered_amount": {str, dict},
        "metaData.delivered_amount.currency": {str},
        "metaData.delivered_amount.issuer": {str},
        "metaData.delivered_amount.value": {str},
    }

class XRPLObjectSchema:
    SCHEMA = {
        "Account": {str},
        "AccountTxnID": {str},
        "Amendments": {list},
        "Amount": {str, dict},
        "Amount.currency": {str},
        "Amount.issuer": {str},
        "Amount.value": {str},
        "Authorize": {str},
        "Balance": {str, dict},
        "Balance.currency": {str},
        "Balance.issuer": {str},
        "Balance.value": {str},
        "BaseFee": {str},
        "BookDirectory": {str},
        "BookNode": {str},
        "BurnedNFTokens": {int},
        "CancelAfter": {int},
        "Condition": {str},
        "Destination": {str},
        "DestinationNode": {str},
        "DestinationTag": {int},
        "Domain": {str},
        "EmailHash": {str},
        "ExchangeRate": {str},
        "Expiration": {int},
        "FinishAfter": {int},
        "FirstLedgerSequence": {int},
        "Flags": {int},
        "Hashes": {list},
        "HighLimit": {dict},
        "HighLimit.currency": {str},
        "HighLimit.issuer": {str},
        "HighLimit.value": {str},
        "HighNode": {str},
        "HighQualityIn": {int},
        "HighQualityOut": {int},
        "IndexNext": {str},
        "IndexPrevious": {str},
        "Indexes": {list},
        "LastLedgerSequence": {int},
        "LedgerEntryType": {str},
        "LowLimit": {dict},
        "LowLimit.currency": {str},
        "LowLimit.issuer": {str},
        "LowLimit.value": {str},
        "LowNode": {str},
        "LowQualityIn": {int},
        "LowQualityOut": {int},
        "MessageKey": {str},
        "MintedNFTokens": {int},
        "NFTokenID": {str},
        "NFTokenMinter": {str},
        "NFTokenOfferNode": {str},
        "NFTokens": {list},
        "NFTokens.NFToken": {dict},
        "NFTokens.NFToken.NFTokenID": {str},
        "NFTokens.NFToken.URI": {str},
        "NextPageMin": {str},
        "Owner": {str},
        "OwnerCount": {int},
        "OwnerNode": {str},
        "PreviousPageMin": {str},
        "PreviousTxnID": {str},
        "PreviousTxnLgrSeq": {int},
        "PublicKey": {str},
        "ReferenceFeeUnits": {int},
        "RegularKey": {str},
        "ReserveBase": {int},
        "ReserveIncrement": {int},
        "RootIndex": {str},
        "SendMax": {str, dict},
        "SendMax.currency": {str},
        "SendMax.issuer": {str},
        "SendMax.value": {str},
        "Sequence": {int},
        "SettleDelay": {int},
        "SignerEntries": {list},
        "SignerEntries.SignerEntry": {dict},
        "SignerEntries.SignerEntry.Account": {str},
        "SignerEntries.SignerEntry.SignerWeight": {int},
        "SignerListID": {int},
        "SignerQuorum": {int},
        "SourceTag": {int},
        "TakerGets": {str, dict},
        "TakerGets.currency": {str},
        "TakerGets.issuer": {str},
        "TakerGets.value": {str},
        "TakerGetsCurrency": {str},
        "TakerGetsIssuer": {str},
        "TakerPays": {str, dict},
        "TakerPays.currency": {str},
        "TakerPays.issuer": {str},
        "TakerPays.value": {str},
        "TakerPaysCurrency": {str},
        "TakerPaysIssuer": {str},
        "TickSize": {int},
        "TicketCount": {int},
        "TicketSequence": {int},
        "TransferRate": {int},
        "WalletLocator": {str},
        "_ExecutionID": {str},
        "_LedgerIndex": {int},
        "_Sequence": {int},
        "index": {str},
    }
