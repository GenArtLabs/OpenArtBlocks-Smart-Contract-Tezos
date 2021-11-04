##
## ## Introduction
##
## See the FA2 standard definition:
## <https://gitlab.com/tzip/tzip/-/blob/master/proposals/tzip-12/>
##
## See more examples/documentation at
## <https://gitlab.com/smondet/fa2-smartpy/> and
## <https://assets.tqtezos.com/docs/token-contracts/fa2/1-fa2-smartpy/>.
##
import smartpy as sp


def bytes_of_nat(params):
    c   = sp.map({x : sp.bytes(hex(x + 48)) for x in range(0, 10)})
    x   = sp.local('x', params)
    res = sp.local('res', [])
    sp.if x.value == 0:
        res.value.push(c[x.value % 10])
    sp.while 0 < x.value:
        res.value.push(c[x.value % 10])
        x.value //= 10
    return sp.concat(res.value)
##
## ## Meta-Programming Configuration
##
## The `FA2_config` class holds the meta-programming configuration.
##
class FA2_config:
    def __init__(self,
                 debug_mode                         = False,
                 non_fungible                       = True,
                 readable                           = True,
                 force_layouts                      = True,
                 support_operator                   = True,
                 store_total_supply                 = True,
                 allow_self_transfer                = False,
                 price                              = 1000000,
                 max_editions                       = 2,
                 base_uri                       = "https://open-artblocks.herokuapp.com/api/",
                 ):

        if debug_mode:
            self.my_map = sp.map
        else:
            self.my_map = sp.big_map
        # The option `debug_mode` makes the code generation use
        # regular maps instead of big-maps, hence it makes inspection
        # of the state of the contract easier.

        self.price = price
        self.max_editions = max_editions
        self.base_uri = base_uri

        self.non_fungible = non_fungible
        # Enforce the non-fungibility of the tokens, i.e. the fact
        # that total supply has to be 1.

        self.readable = readable
        # The `readable` option is a legacy setting that we keep around
        # only for benchmarking purposes.
        #
        # User-accounts are kept in a big-map:
        # `(user-address * token-id) -> ownership-info`.
        #
        # For the Babylon protocol, one had to use `readable = False`
        # in order to use `PACK` on the keys of the big-map.

        self.force_layouts = force_layouts
        # The specification requires all interface-fronting records
        # and variants to be *right-combs;* we keep
        # this parameter to be able to compare performance & code-size.

        self.support_operator = support_operator
        # The operator entry-points always have to be there, but there is
        # definitely a use-case for having them completely empty (saving
        # storage and gas when `support_operator` is `False).

        self.store_total_supply = store_total_supply
        # Whether to store the total-supply for each token (next to
        # the token-metadata).

        self.add_mutez_transfer = True
        # Add an entry point for the administrator to transfer tez potentially
        # in the contract's balance.

        self.allow_self_transfer = allow_self_transfer
        # Authorize call of `transfer` entry_point from self
        name = "FA2"
        if debug_mode:
            name += "-debug"
        if non_fungible:
            name += "-nft"
        if not readable:
            name += "-no_readable"
        if not force_layouts:
            name += "-no_layout"
        if not support_operator:
            name += "-no_ops"
        if not store_total_supply:
            name += "-no_totsup"
        if allow_self_transfer:
            name += "-self_transfer"
        self.name = name

## ## Auxiliary Classes and Values
##
## The definitions below implement SmartML-types and functions for various
## important types.
##
token_id_type = sp.TNat

class Error_message:
    def __init__(self, config):
        self.config = config
        self.prefix = "FA2_"
    def make(self, s): return (self.prefix + s)
    def token_undefined(self):       return self.make("TOKEN_UNDEFINED")
    def insufficient_balance(self):  return self.make("INSUFFICIENT_BALANCE")
    def not_operator(self):          return self.make("NOT_OPERATOR")
    def not_owner(self):             return self.make("NOT_OWNER")
    def bad_value(self):             return self.make("BAD_VALUE")
    def max_editions_reached(self):  return self.make("MAX_EDITIONS_REACHED")
    def operators_unsupported(self): return self.make("OPERATORS_UNSUPPORTED")
    def not_admin(self):             return self.make("NOT_ADMIN")
    def not_admin_or_operator(self): return self.make("NOT_ADMIN_OR_OPERATOR")
    def paused(self):                return self.make("PAUSED")
    def locked(self):                return self.make("LOCKED")
    def bad_amount(self):           return self.make("BAD_QUANTITY")

## The current type for a batched transfer in the specification is as
## follows:
##
## ```ocaml
## type transfer = {
##   from_ : address;
##   txs: {
##     to_ : address;
##     token_id : token_id;
##     amount : nat;
##   } list
## } list
## ```
##
## This class provides helpers to create and force the type of such elements.
## It uses the `FA2_config` to decide whether to set the right-comb layouts.
class Batch_transfer:
    def __init__(self, config):
        self.config = config
    def get_transfer_type(self):
        tx_type = sp.TRecord(to_ = sp.TAddress,
                             token_id = token_id_type,
                             amount = sp.TNat)
        if self.config.force_layouts:
            tx_type = tx_type.layout(
                ("to_", ("token_id", "amount"))
            )
        transfer_type = sp.TRecord(from_ = sp.TAddress,
                                   txs = sp.TList(tx_type)).layout(
                                       ("from_", "txs"))
        return transfer_type
    def get_type(self):
        return sp.TList(self.get_transfer_type())
    def item(self, from_, txs):
        v = sp.record(from_ = from_, txs = txs)
        return sp.set_type_expr(v, self.get_transfer_type())
##
## `Operator_param` defines type types for the `%update_operators` entry-point.
class Operator_param:
    def __init__(self, config):
        self.config = config
    def get_type(self):
        t = sp.TRecord(
            owner = sp.TAddress,
            operator = sp.TAddress,
            token_id = token_id_type)
        if self.config.force_layouts:
            t = t.layout(("owner", ("operator", "token_id")))
        return t
    def make(self, owner, operator, token_id):
        r = sp.record(owner = owner,
                      operator = operator,
                      token_id = token_id)
        return sp.set_type_expr(r, self.get_type())

## The link between operators and the addresses they operate is kept
## in a *lazy set* of `(owner × operator × token-id)` values.
##
## A lazy set is a big-map whose keys are the elements of the set and
## values are all `Unit`.
class Operator_set:
    def __init__(self, config):
        self.config = config
    def inner_type(self):
        return sp.TRecord(owner = sp.TAddress,
                          operator = sp.TAddress,
                          token_id = token_id_type
                          ).layout(("owner", ("operator", "token_id")))
    def key_type(self):
        if self.config.readable:
            return self.inner_type()
        else:
            return sp.TBytes
    def make(self):
        return self.config.my_map(tkey = self.key_type(), tvalue = sp.TUnit)
    def make_key(self, owner, operator, token_id):
        metakey = sp.record(owner = owner,
                            operator = operator,
                            token_id = token_id)
        metakey = sp.set_type_expr(metakey, self.inner_type())
        if self.config.readable:
            return metakey
        else:
            return sp.pack(metakey)
    def add(self, set, owner, operator, token_id):
        set[self.make_key(owner, operator, token_id)] = sp.unit
    def remove(self, set, owner, operator, token_id):
        del set[self.make_key(owner, operator, token_id)]
    def is_member(self, set, owner, operator, token_id):
        return set.contains(self.make_key(owner, operator, token_id))

class Balance_of:
    def request_type():
        return sp.TRecord(
            owner = sp.TAddress,
            token_id = token_id_type).layout(("owner", "token_id"))
    def response_type():
        return sp.TList(
            sp.TRecord(
                request = Balance_of.request_type(),
                balance = sp.TNat).layout(("request", "balance")))
    def entry_point_type():
        return sp.TRecord(
            callback = sp.TContract(Balance_of.response_type()),
            requests = sp.TList(Balance_of.request_type())
        ).layout(("requests", "callback"))

class Token_meta_data:
    def __init__(self, config):
        self.config = config

    def get_type(self):
        return sp.TRecord(token_id = sp.TNat, token_info = sp.TMap(sp.TString, sp.TBytes))

    def set_type_and_layout(self, expr):
        sp.set_type(expr, self.get_type())

## The set of all tokens is represented by a `nat` if we assume that token-ids
## are consecutive, or by an actual `(set nat)` if not.
##
## - Knowing the set of tokens is useful for throwing accurate error messages.
## - Previous versions of the specification required this set for functional
##   behavior (operators interface had to deal with “all tokens”).
class Token_id_set:
    def __init__(self, config):
        self.config = config
    def empty(self):
        return sp.nat(0)
    def add(self, totalTokens, tokenID):
        sp.verify(totalTokens == tokenID, message = "Token-IDs should be consecutive")
        totalTokens.set(tokenID + 1)
    def contains(self, totalTokens, tokenID):
        return (tokenID < totalTokens)
    def cardinal(self, totalTokens):
        return totalTokens

##
## ## Implementation of the Contract
##
## `mutez_transfer` is an optional entry-point, hence we define it “outside” the
## class:
def mutez_transfer(contract, params):
    sp.verify(sp.sender == contract.data.administrator)
    sp.set_type(params.destination, sp.TAddress)
    sp.set_type(params.amount, sp.TMutez)
    sp.send(params.destination, params.amount)
##
## The `FA2` class builds a contract according to an `FA2_config` and an
## administrator address.
## It is inheriting from `FA2_core` which implements the strict
## standard and a few other classes to add other common features.
##
## - We see the use of
##   [`sp.entry_point`](https://smartpy.io/docs/introduction/entry_points)
##   as a function instead of using annotations in order to allow
##   optional entry points.
## - The storage field `metadata_string` is a placeholder, the build
##   system replaces the field annotation with a specific version-string, such
##   as `"version_20200602_tzip_b916f32"`: the version of FA2-smartpy and
##   the git commit in the TZIP [repository](https://gitlab.com/tzip/tzip) that
##   the contract should obey.
class FA2_core(sp.Contract):
    def __init__(self, config, metadata, **extra_storage):
        self.config = config
        self.error_message = Error_message(self.config)
        self.operator_set = Operator_set(self.config)
        self.operator_param = Operator_param(self.config)
        self.token_id_set = Token_id_set(self.config)
        # TODO understand self.ledger_key = Ledger_key(self.config)
        self.token_meta_data = Token_meta_data(self.config)
        self.batch_transfer    = Batch_transfer(self.config)
        if  self.config.add_mutez_transfer:
            self.transfer_mutez = sp.entry_point(mutez_transfer)
        self.add_flag("initial-cast")
        self.exception_optimization_level = "default-line"
        self.init(
            ledger = self.config.my_map(tkey = sp.TNat, tvalue = sp.TAddress),
            hashes = self.config.my_map(tkey = sp.TNat, tvalue = sp.TBytes),
            operators = self.operator_set.make(),
            all_tokens = self.token_id_set.empty(),
            metadata = metadata,
            price = self.config.price,
            max_editions = self.config.max_editions,
            script = sp.string(""),
            base_uri = sp.utils.bytes_of_string(self.config.base_uri),
            **extra_storage
        )

        if self.config.store_total_supply:
            self.update_initial_storage(
                total_supply = self.config.my_map(tkey = sp.TNat, tvalue = sp.TNat),
            )

    @sp.entry_point
    def transfer(self, params):
        sp.set_type(params, self.batch_transfer.get_type())
        sp.for transfer in params:
           sp.for tx in transfer.txs:

                sender_verify = (
                    (transfer.from_ == sp.sender) |
                    self.operator_set.is_member(self.data.operators,
                        transfer.from_,
                        sp.sender,
                        tx.token_id)
                )
                message = self.error_message.not_operator()

                if self.config.allow_self_transfer:
                    sender_verify |= (sp.sender == sp.self_address)
                sp.verify(sender_verify, message = message)
                sp.verify(
                    self.data.hashes.contains(tx.token_id),
                    message = self.error_message.token_undefined()
                )
                sp.verify(tx.amount <= 1, message = self.error_message.insufficient_balance())

                sp.if (tx.amount == 1):

                    sp.verify(
                        (self.data.ledger[tx.token_id] == transfer.from_),
                        message = self.error_message.insufficient_balance())
                    self.data.ledger[tx.token_id] = tx.to_
                sp.else:
                    pass

    @sp.entry_point
    def balance_of(self, params):
        sp.set_type(params, Balance_of.entry_point_type())
        def f_process_request(req):
            sp.verify(self.data.hashes.contains(req.token_id), message = self.error_message.token_undefined())
            sp.if self.data.ledger[req.token_id] == req.owner:
                sp.result(
                    sp.record(
                        request = sp.record(
                            owner = sp.set_type_expr(req.owner, sp.TAddress),
                            token_id = sp.set_type_expr(req.token_id, sp.TNat)),
                        balance = 1))
            sp.else:
                sp.result(
                    sp.record(
                        request = sp.record(
                            owner = sp.set_type_expr(req.owner, sp.TAddress),
                            token_id = sp.set_type_expr(req.token_id, sp.TNat)),
                        balance = 0))
        res = sp.local("responses", params.requests.map(f_process_request))
        destination = sp.set_type_expr(params.callback, sp.TContract(Balance_of.response_type()))
        sp.transfer(res.value, sp.mutez(0), destination)

    @sp.offchain_view(pure = True)
    def get_balance(self, req):
        """This is the `get_balance` view defined in TZIP-12."""
        sp.set_type(
            req, sp.TRecord(
                owner = sp.TAddress,
                token_id = sp.TNat
            ).layout(("owner", "token_id")))
        sp.verify(self.data.hashes.contains(req.token_id), message = self.error_message.token_undefined())
        sp.if self.data.ledger[req.token_id] == req.owner:
            sp.result(1)
        sp.else:
            sp.result(0)

    @sp.entry_point
    def update_operators(self, params):
        sp.set_type(params, sp.TList(
            sp.TVariant(
                add_operator = self.operator_param.get_type(),
                remove_operator = self.operator_param.get_type()
            )
        ))
        if self.config.support_operator:
            sp.for update in params:
                with update.match_cases() as arg:
                    with arg.match("add_operator") as upd:
                        sp.verify(upd.owner == sp.sender, message = self.error_message.not_owner())
                        self.operator_set.add(self.data.operators,
                                              upd.owner,
                                              upd.operator,
                                              upd.token_id)
                    with arg.match("remove_operator") as upd:
                        sp.verify(upd.owner == sp.sender, message = self.error_message.not_owner())
                        self.operator_set.remove(self.data.operators,
                                                 upd.owner,
                                                 upd.operator,
                                                 upd.token_id)
        else:
            sp.failwith(self.error_message.operators_unsupported())

    # this is not part of the standard but can be supported through inheritance.
    def is_paused(self):
        return sp.bool(False)

    # this is not part of the standard but can be supported through inheritance.
    def is_administrator(self, sender):
        return sp.bool(False)

class FA2_administrator(FA2_core):
    def is_administrator(self, sender):
        return sender == self.data.administrator

    @sp.entry_point
    def set_administrator(self, params):
        sp.verify(self.is_administrator(sp.sender), message = self.error_message.not_admin())
        self.data.administrator = params

class FA2_pause(FA2_core):
    def is_paused(self):
        return self.data.paused

    @sp.entry_point
    def set_pause(self, params):
        sp.verify(self.is_administrator(sp.sender), message = self.error_message.not_admin())
        self.data.paused = params

class FA2_lock(FA2_core):
    def is_locked(self):
        return self.data.locked

    @sp.entry_point
    def lock(self):
        sp.verify(self.is_administrator(sp.sender), message = self.error_message.not_admin())
        self.data.locked = sp.bool(True)

class FA2_mint(FA2_core):
    @sp.entry_point
    def mint(self, amount):
        sp.set_type(amount, sp.TInt)
        sp.verify(amount > 0, message = self.error_message.bad_amount())

        sp.verify(~ self.is_paused(), message = self.error_message.paused())

        nat_amount = sp.as_nat(amount, message = self.error_message.bad_amount())
        sp.verify(sp.amount == sp.mul(sp.mutez(self.config.price), nat_amount), message = self.error_message.bad_value())
        sp.verify(self.data.all_tokens + nat_amount <= self.config.max_editions, message = self.error_message.max_editions_reached())

        i = sp.compute(amount)
        sp.while i > 0:
            token_id = sp.compute(self.data.all_tokens)
            sp.verify(token_id < self.config.max_editions, message = self.error_message.max_editions_reached())

            token_hash = sp.keccak(sp.pack(sp.record(now=sp.now, s=sp.sender, tid=token_id)))

            self.data.ledger[token_id] = sp.sender
            self.data.hashes[token_id] = token_hash
            self.token_id_set.add(self.data.all_tokens, token_id)

            i.set(i - 1)


class FA2_script(FA2_core):
    @sp.entry_point
    def set_script(self, script):
        sp.verify(~ self.is_locked(), message = self.error_message.locked())
        sp.verify(self.is_administrator(sp.sender), message = self.error_message.not_admin())
        sp.set_type(script, sp.TString)
        self.data.script.set(script)

class FA2_base_uri(FA2_core):
    @sp.entry_point
    def set_base_uri(self, params):
        sp.set_type(params, sp.TBytes)
        sp.verify(~ self.is_locked(), message = self.error_message.locked())
        sp.verify(self.is_administrator(sp.sender), message = self.error_message.not_admin())
        self.data.base_uri = params

class FA2_token_metadata(FA2_core):
    def set_token_metadata_view(self):
        def token_metadata(self, token_id):
            """
            Return the token-metadata URI for the given token.

            For a reference implementation, dynamic-views seem to be the
            most flexible choice.
            """
            sp.set_type(token_id, sp.TNat)

            sp.verify(token_id < self.data.all_tokens, message = self.error_message.token_undefined())
            token_hash = self.data.hashes[token_id]

            metadata = FA2.make_metadata(
                name = "Tezticule",
                decimals = 0,
                symbol= "TIK",
                token_hash = token_hash,
                uri = self.data.base_uri + bytes_of_nat(token_id)
            )

            sp.result(sp.record(token_id  = token_id, token_info = metadata))

        self.token_metadata = sp.offchain_view(pure = True, doc = "Get Token Metadata")(token_metadata)

    def make_metadata(symbol, name, decimals, token_hash, uri):
        "Helper function to build metadata JSON bytes values."
        return (sp.map(l = {
            # Remember that michelson wants map already in ordered
            "decimals" : sp.utils.bytes_of_string("%d" % decimals),
            "name" : sp.utils.bytes_of_string(name),
            "symbol" : sp.utils.bytes_of_string(symbol),
            "token_hash" : token_hash,
            "" : uri,
        }))


class FA2(FA2_token_metadata, FA2_mint, FA2_administrator, FA2_pause, FA2_lock, FA2_script, FA2_base_uri, FA2_core):

    @sp.offchain_view(pure = True)
    def count_tokens(self):
        """Get how many tokens are in this FA2 contract.
        """
        sp.result(self.token_id_set.cardinal(self.data.all_tokens))

    @sp.offchain_view(pure = True)
    def does_token_exist(self, tok):
        "Ask whether a token ID is exists."
        sp.set_type(tok, sp.TNat)
        sp.result(self.data.hashes.contains(tok))

    @sp.offchain_view(pure = True)
    def all_tokens(self):
        sp.result(sp.range(0, self.data.all_tokens))

    @sp.offchain_view(pure = True)
    def total_supply(self, tok):
        if self.config.store_total_supply:
            sp.result(self.data.total_supply[tok])
        else:
            sp.set_type(tok, sp.TNat)
            sp.result("total-supply not supported")

    @sp.offchain_view(pure = True)
    def is_operator(self, query):
        sp.set_type(query,
                    sp.TRecord(token_id = sp.TNat,
                               owner = sp.TAddress,
                               operator = sp.TAddress).layout(
                                   ("owner", ("operator", "token_id"))))
        sp.result(
            self.operator_set.is_member(self.data.operators,
                                        query.owner,
                                        query.operator,
                                        query.token_id)
        )

    def __init__(self, config, metadata, admin):
        # Let's show off some meta-programming:
        self.all_tokens.doc = """
        This view is specified (but optional) in the standard.
        """
        list_of_views = [
            self.get_balance
            , self.does_token_exist
            , self.count_tokens
            , self.all_tokens
            , self.is_operator
        ]

        if config.store_total_supply:
            list_of_views = list_of_views + [self.total_supply]
        self.set_token_metadata_view()
        list_of_views = list_of_views + [self.token_metadata]

        metadata_base = {
            "version": config.name # will be changed if using fatoo.
            , "description" : (
                "This is a didactic reference implementation of FA2,"
                + " a.k.a. TZIP-012, using SmartPy.\n\n"
                + "This particular contract uses the configuration named: "
                + config.name + "."
            )
            , "interfaces": ["TZIP-012", "TZIP-016"]
            , "authors": [
                "Seb Mondet <https://seb.mondet.org>"
            ]
            , "homepage": "https://gitlab.com/smondet/fa2-smartpy"
            , "views": list_of_views
            , "source": {
                "tools": ["SmartPy"]
                , "location": "https://gitlab.com/smondet/fa2-smartpy.git"
            }
            , "permissions": {
                "operator":
                "owner-or-operator-transfer" if config.support_operator else "owner-transfer"
                , "receiver": "owner-no-hook"
                , "sender": "owner-no-hook"
            }
            , "fa2-smartpy": {
                "configuration" :
                dict([(k, getattr(config, k)) for k in dir(config) if "__" not in k and k != 'my_map'])
            }
        }
        self.init_metadata("metadata_base", metadata_base)
        FA2_core.__init__(self, config, metadata, paused = False, locked = False, administrator = admin)

## ## Tests
##
## ### Auxiliary Consumer Contract
##
## This contract is used by the tests to be on the receiver side of
## callback-based entry-points.
## It stores facts about the results in order to use `scenario.verify(...)`
## (cf.
##  [documentation](https://smartpy.io/docs/scenarios/testing)).
class View_consumer(sp.Contract):
    def __init__(self, contract):
        self.contract = contract
        self.init(last_sum = 0,
                  operator_support =  not contract.config.support_operator)

    @sp.entry_point
    def reinit(self):
        self.data.last_sum = 0
        # It's also nice to make this contract have more than one entry point.

    @sp.entry_point
    def receive_balances(self, params):
        sp.set_type(params, Balance_of.response_type())
        self.data.last_sum = 0
        sp.for resp in params:
            self.data.last_sum += resp.balance

## ### Generation of Test Scenarios
##
## Tests are also parametrized by the `FA2_config` object.
## The best way to visualize them is to use the online IDE
## (<https://www.smartpy.io/ide/>).
def add_test(config, is_default = True):
    def get_addresses():
        # sp.test_account generates ED25519 key-pairs deterministically:
        admin = sp.test_account("Administrator")
        alice = sp.test_account("Alice")
        bob   = sp.test_account("Robert")
        return admin, [alice, bob]

    def ownership_test(scenario, contract, ledgers, quiet=False):
            if not quiet:
                scenario.p("Tokens ownership test")
            for i in range(len(ledgers)):
                scenario.verify(contract.data.ledger[i] == ledgers[i].address)

    @sp.add_test(name = "Basic test", is_default = is_default)
    def basic_test():
        scenario = sp.test_scenario()
        scenario.h1("FA2 Contract Name: " + config.name)
        scenario.table_of_contents()

        admin, [alice, bob] = get_addresses()

        # Let's display the accounts:
        scenario.h2("Accounts")
        scenario.show([admin, alice, bob])
        c1 = FA2(config = config,
                 metadata = sp.utils.metadata_of_url("https://example.com"),
                 admin = admin.address)
        scenario += c1

        stringUrl = 'https://yo.com/api/'
        url = sp.bytes('0x' + ''.join([hex(ord(c))[2:] for c in stringUrl]))
        c1.set_base_uri(url).run(sender = admin)

        scenario.h2("Mint")
        minted = c1.mint(1).run(sender = alice, amount = sp.mutez(1000000))
        scenario.verify(c1.data.ledger[0] == alice.address)

        scenario.h2("Set base URI")
        resultingUri = c1.token_metadata(0).token_info['']
        scenario.verify(resultingUri == sp.bytes('0x' + ''.join([hex(ord(c))[2:] for c in stringUrl + '0'])))

        scenario.h2("Fail because of bad price")
        c1.mint(1).run(sender = alice, amount = sp.mutez(2), valid = False)

        scenario.h2("Test ledger")
        c1.mint(1).run(sender = alice, amount = sp.mutez(1000000))
        scenario.verify(c1.data.ledger[0] == alice.address)
        scenario.verify(c1.data.ledger[1] == alice.address)

        scenario.h2("Mint when max number of token reached")
        c1.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid = False)

    @sp.add_test(name = "Tests pause", is_default = is_default)
    def tests_pause():
        scenario = sp.test_scenario()

        admin, [alice, bob] = get_addresses()

        config.max_editions = 10000
        c1 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)

        scenario.h1("Tests pause")
        scenario.table_of_contents()

        scenario += c1

        scenario.h2("Mint without pause")
        minted = c1.mint(1).run(sender = alice, amount = sp.mutez(1000000))
        scenario.verify(c1.data.ledger[0] == alice.address)

        scenario.h2("Pause")

        scenario.h3("Activation")
        c1.set_pause(True).run(sender = admin, valid = True)

        scenario.h3("Mint not possible")
        c1.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid=False)
        c1.mint(1).run(sender = admin, amount = sp.mutez(1000000), valid=False)

        scenario.h2("Pause activation while pause is already active")

        scenario.h3("Over-activation")
        c1.set_pause(True).run(sender = admin, valid = True)

        scenario.h3("Mint still not possible")
        c1.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid=False)

        scenario.h2("Pause de-activation")
        c1.set_pause(False).run(sender = admin, valid = True)

        scenario.h3("Mint possible again")
        c1.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid=True)
        c1.mint(1).run(sender = admin, amount = sp.mutez(1000000), valid=True)

        scenario.h2("Pause from non-admin")
        c1.set_pause(True).run(sender = alice, valid = False)

        scenario.h2("Pause deactivation from non-admin")
        c1.set_pause(True).run(sender = admin, valid = True)
        c1.set_pause(False).run(sender = alice, valid = False)

        scenario.h2("Behaviour when all token minted (kinda useless)")
        config.max_editions = 0 # Go out of tokens
        c2 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)

        scenario += c2

        c2.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid=False)

        scenario.h3("Activation from admin")
        c2.set_pause(True).run(sender = admin, valid = True)
        c2.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid=False)

        scenario.h3("Deactivation from admin")
        c2.set_pause(False).run(sender = admin, valid = True)

        scenario.h3("Activation from non-admin")
        c2.set_pause(True).run(sender = alice, valid = False)

        scenario.h3("Deactivation from non-admin")
        c2.set_pause(True).run(sender = admin, valid = True)
        c2.set_pause(False).run(sender = alice, valid = False)

        scenario.h2("Behaviour when contract is locked")
        # Reset minted tokens
        config.max_editions = 1000
        c3 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)

        scenario += c3

        c3.lock().run(sender = admin, valid = True)

        scenario.h3("Activation from admin")
        c3.set_pause(True).run(sender = admin, valid = True)

        scenario.h3("Mint not possible")
        c3.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid=False)

        scenario.h3("Deactivation from admin")
        c3.set_pause(False).run(sender = admin, valid = True)

        scenario.h3("Mint possible")
        c3.mint(1).run(sender = alice, amount = sp.mutez(1000000))

        scenario.h3("Activation from non-admin")
        c3.set_pause(True).run(sender = alice, valid = False)

        scenario.h3("Deactivation from non-admin")
        c3.set_pause(True).run(sender = admin, valid = True)
        c3.set_pause(False).run(sender = alice, valid = False)

    def set_and_test_base_uri(stringUrl, scenario, contract, sender, valid = True):
        url = sp.bytes('0x' + ''.join([hex(ord(c))[2:] for c in stringUrl]))
        contract.set_base_uri(url).run(sender = sender, valid = valid)
        expectedUri = sp.bytes('0x' + ''.join([hex(ord(c))[2:] for c in stringUrl + '0']))
        resultingUri = contract.token_metadata(0).token_info['']
        if (valid):
            scenario.verify(resultingUri == expectedUri)
        else:
            scenario.verify(resultingUri != expectedUri)

    def set_and_test_script(newScript, scenario, contract, sender, valid = True):
        contract.set_script(newScript).run(sender = sender, valid = valid)
        resultingScript = contract.data.script
        if (valid):
            scenario.verify(resultingScript == newScript)
        else:
            scenario.verify(resultingScript != newScript)

    @sp.add_test(name = "Lock test", is_default = is_default)
    def lock_test():
        scenario = sp.test_scenario()
        scenario.h1("Lock test")
        scenario.table_of_contents()

        admin, [alice, bob] = get_addresses()

        config.max_editions = 10000

        c1 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)
        scenario += c1

        scenario.h2("Initial minting")
        minted = c1.mint(1).run(sender = alice, amount = sp.mutez(1000000))

        scenario.h3("set_base_uri without lock")
        set_and_test_base_uri('https://example1.com/api/', scenario, c1, admin)
        set_and_test_script('alert(1);', scenario, c1, admin)

        scenario.h2("Lock")

        scenario.h3("Lock from non-admin")
        c1.lock().run(sender = alice, valid = False)

        scenario.h3("set_base_uri still possible")
        set_and_test_base_uri('https://example2.com/api/', scenario, c1, admin)
        set_and_test_script('alert(2);', scenario, c1, admin)

        scenario.h3("Lock from admin")
        c1.lock().run(sender = admin)

        scenario.h3("set_base_uri impossible with lock")
        set_and_test_base_uri('https://example3.com/api/', scenario, c1, admin, False)
        set_and_test_script('alert(3);', scenario, c1, admin, False)

        scenario.h2("Lock activation when lock is already active")

        scenario.h3("Over-activation")
        c1.lock().run(sender = admin)

        scenario.h3("set_base_uri still impossible with lock")
        set_and_test_base_uri('https://example4.com/api/', scenario, c1, admin, False)
        set_and_test_script('alert(4);', scenario, c1, admin, False)

        scenario.h2("Lock when all tokens are minted (new contract)")
        config.max_editions = 1
        c2 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)
        scenario += c2

        scenario.h3("set_base_uri possible when all tokens have been minted")
        c2.mint(1).run(sender = alice, amount = sp.mutez(1000000))
        c2.mint(1).run(sender = alice, amount = sp.mutez(1000000), valid=False)
        set_and_test_base_uri('https://example1.com/api/', scenario, c2, admin)
        set_and_test_script('alert(1);', scenario, c2, admin)

        scenario.h3("Lock from non-admin")
        c2.lock().run(sender = alice, valid = False)

        scenario.h3("set_base_uri still possible")
        set_and_test_base_uri('https://example2.com/api/', scenario, c2, admin)
        set_and_test_script('alert(2);', scenario, c2, admin)

        scenario.h3("Lock from admin")
        c2.lock().run(sender = admin, valid = True)

        scenario.h3("set_base_uri impossible with lock")
        set_and_test_base_uri('https://example3.com/api/', scenario, c2, admin, False)
        set_and_test_script('alert(3);', scenario, c2, admin, False)

    @sp.add_test(name = "Mint test", is_default = is_default)
    def mint_test():
        scenario = sp.test_scenario()
        scenario.h1("Mint test")
        scenario.table_of_contents()

        admin, [alice, bob] = get_addresses()

        config.max_editions = 10000
        c1 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)
        scenario += c1

        scenario.h2("Single minting")
        scenario.h3("Mint 1 token from non-admin (OK)")
        c1.mint(1).run(sender = alice, amount = sp.mutez(config.price))
        scenario.verify(c1.data.ledger[0] == alice.address)
        scenario.h3("Mint 1 token from admin (OK)")
        c1.mint(1).run(sender = admin, amount = sp.mutez(config.price))
        scenario.verify(c1.data.ledger[1] == admin.address)

        scenario.h2("Negative minting")
        scenario.h3("Mint -1 tokens from non-admin (KO)")
        c1.mint(-1).run(sender = alice, amount = sp.mutez(0), valid = False)
        scenario.h3("Mint -1 tokens from admin (KO)")
        c1.mint(-1).run(sender = admin, amount = sp.mutez(0), valid = False)

        scenario.h2("Zero minting")
        scenario.h3("Mint 0 tokens from non-admin (KO)")
        c1.mint(0).run(sender = alice, amount = sp.mutez(0), valid = False)
        scenario.h3("Mint 0 tokens from admin (KO)")
        c1.mint(0).run(sender = admin, amount = sp.mutez(0), valid = False)

        scenario.h2("Multiple minting")
        scenario.h3("Mint 3 tokens from non-admin (OK)")
        c1.mint(3).run(sender = alice, amount = sp.mutez(config.price * 3))
        for i in range(2, 5):
            scenario.verify(c1.data.ledger[i] == alice.address)
        scenario.h3("Mint 11 tokens from non-admin (OK)")
        c1.mint(11).run(sender = alice, amount = sp.mutez(config.price * 11))
        for i in range(5, 16):
            scenario.verify(c1.data.ledger[i] == alice.address)

        if (config.price > 0):
            scenario.h2("Incoherent amount (0)")
            scenario.h3("Mint 1 token from non-admin for amount=0 (KO)")
            c1.mint(1).run(sender = alice, amount = sp.mutez(0), valid = False)
            scenario.h3("Mint 1 token from admin for amount=0 (KO)")
            c1.mint(1).run(sender = admin, amount = sp.mutez(0), valid = False)

            scenario.h2("Incoherent amount (lower)")
            scenario.h3("Mint 1 token from non-admin for amount=price-1 (KO)")
            c1.mint(1).run(sender = alice, amount = sp.mutez(config.price - 1), valid = False)
            scenario.h3("Mint 1 token from admin for amount=price-1 (KO)")
            c1.mint(1).run(sender = admin, amount = sp.mutez(config.price - 1), valid = False)

        scenario.h2("Incoherent amount (greater)")
        scenario.h3("Mint 1 token from non-admin for amount=price+1 (KO)")
        c1.mint(1).run(sender = alice, amount = sp.mutez(config.price + 1), valid = False)
        scenario.h3("Mint 1 token from admin for amount=price+1 (KO)")
        c1.mint(1).run(sender = admin, amount = sp.mutez(config.price + 1), valid = False)

        scenario.h2("Pause")
        scenario.h3("Pause activation from admin (OK)")
        c1.set_pause(True).run(sender = admin)
        scenario.h3("Mint 1 token from non-admin (KO)")
        c1.mint(1).run(sender = alice, amount = sp.mutez(config.price), valid = False)
        scenario.h3("Mint 1 token from admin (KO)")
        c1.mint(1).run(sender = admin, amount = sp.mutez(config.price), valid = False)

        scenario.h2("Unpause")
        scenario.h3("Pause deactivation from admin (OK)")
        c1.set_pause(False).run(sender = admin)
        scenario.h3("Mint 1 token from non-admin (OK)")
        c1.mint(1).run(sender = alice, amount = sp.mutez(config.price))
        scenario.verify(c1.data.ledger[16] == alice.address)
        scenario.h3("Mint 1 token from admin (OK)")
        c1.mint(1).run(sender = admin, amount = sp.mutez(config.price))
        scenario.verify(c1.data.ledger[17] == admin.address)

        scenario.h2("Max editions reached (new contract with max_editions=1)")
        config.max_editions = 1
        c2 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)
        scenario += c2

        scenario.h3("Mint more tokens than available")
        scenario.h4("Mint 2 tokens from non-admin (KO)")
        c2.mint(2).run(sender = alice, amount = sp.mutez(config.price * 2), valid = False)
        scenario.h4("Mint 2 tokens from admin (KO)")
        c2.mint(2).run(sender = admin, amount = sp.mutez(config.price * 2), valid = False)

        scenario.h3("Mint until max is reached")
        scenario.h4("Mint 1 token from non-admin (OK)")
        c2.mint(1).run(sender = alice, amount = sp.mutez(config.price))
        scenario.verify(c1.data.ledger[0] == alice.address)

        scenario.h3("Mint 1 token after max is reached")
        scenario.h4("Mint 1 token from non-admin (KO)")
        c2.mint(1).run(sender = alice, amount = sp.mutez(config.price), valid = False)
        scenario.h4("Mint 1 token from admin (KO)")
        c2.mint(1).run(sender = admin, amount = sp.mutez(config.price), valid = False)

    @sp.add_test(name = "tzip12 tests transfer", is_default = is_default)
    def tests_transfer():
        scenario = sp.test_scenario()

        admin, [alice, bob] = get_addresses()

        config.max_editions = 10000
        c1 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)

        scenario.h1("Tests transfer")
        scenario.table_of_contents()

        scenario += c1

        scenario.h2("Initial Minting")
        scenario.p("Alice mints a token")
        c1.mint(1).run(sender = alice, amount = sp.mutez(1000000))

        scenario.p("Bob mints a token")
        c1.mint(1).run(sender = bob, amount = sp.mutez(1000000))

        scenario.p("Admin mints a token")
        c1.mint(1).run(sender = admin, amount = sp.mutez(1000000))

        possessors = [alice, bob, admin]
        ownership_test(scenario, c1, possessors)

        scenario.h2("Simple transfer")

        scenario.h3("Valid testcases")

        scenario.h4("Alice sends its token to Bob")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice)
        possessors[0] = bob
        ownership_test(scenario, c1, possessors)

        scenario.h4("Bob sends its initial token to Alice")
        c1.transfer([
                c1.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 1)
                                    ])
            ]).run(sender = bob)
        possessors[1] = alice
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice sends a token to itself")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 1)
                                    ])
            ]).run(sender = alice)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice sends its token in 0 amount to someone")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 0,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice sends a Bob's token in 0 amount to someone")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 0,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Invalid testcases")

        scenario.h4("Alice tries to send a non-existing token in 0 amount to someone")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 0,
                                                token_id = 1000)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice tries to send twice its token (amount) to someone")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 2,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice tries to send twice its token (amount) to itself")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 2,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice tries to send its initial token to Bob")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice tries to steal a token from Bob")
        c1.transfer([
                c1.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice tries to transfer a non-existing token")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 1000)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice tries to self-transfer a non-existing token")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 1000)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h4("Alice tries to steal a non-existing token from Bob")
        c1.transfer([
                c1.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 1000)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h2("Test existencee of admin special rights")

        scenario.h3("Admin tries to steal a token from Alice")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 1)
                                    ])
            ]).run(sender = admin, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Admin tries to force Alice to give a token to Bob")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 1)
                                    ])
            ]).run(sender = admin, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Alice tries to transfer a non-existing token")
        c1.transfer([
                c1.batch_transfer.item(from_ = admin.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 1000)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Admin tries to self-transfer a non-existing token")
        c1.transfer([
                c1.batch_transfer.item(from_ = admin.address,
                                    txs = [
                                        sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 1000)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Admin tries to steal a non-existing token from Bob")
        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 1000)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h2("Multiple transfer")

        # Reset contract
        config.max_editions = 10000
        c2 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)

        scenario += c2

        scenario.p("Alice mints 3 tokens")
        c2.mint(3).run(sender = alice, amount = sp.mutez(3000000))

        scenario.p("Bob mints 2 tokens")
        c2.mint(2).run(sender = bob, amount = sp.mutez(2000000))

        scenario.p("Admin mints 1 token")
        c2.mint(1).run(sender = admin, amount = sp.mutez(1000000))
        possessors = [alice]*3 + [bob]*2 + [admin]
        ownership_test(scenario, c2, possessors)

        scenario.h3("Valid cases")

        scenario.h4("Alice sends 2 tokens to Bob")
        c2.transfer([
                c2.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ] + [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 1)
                                    ])
            ]).run(sender = alice)
        possessors[0] = bob
        possessors[1] = bob
        ownership_test(scenario, c2, possessors)

        scenario.h4("Alice sends 2 times the same token to itself")
        c2.transfer([
                c2.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 2)
                                    ] + [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 2)
                                    ])
            ]).run(sender = alice)
        ownership_test(scenario, c2, possessors)

        scenario.h4("Bob sends 1 token to Alice and 1 token to Admin")
        c2.transfer([
                c2.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 3)
                                    ] + [
                                        sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 4)
                                    ])
            ]).run(sender = bob)
        possessors[3] = alice
        possessors[4] = admin
        ownership_test(scenario, c2, possessors)

        scenario.h4("Bob sends 1 token to Admin and twice the same token to itself")
        c2.transfer([
                c2.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 1)
                                    ] + [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ] + [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = bob)
        possessors[1] = admin
        ownership_test(scenario, c2, possessors)

        scenario.h4("Alice sends the same token to both itself and Bob")
        c2.transfer([
                c2.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 2)
                                    ] + [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 2)
                                    ])
            ]).run(sender = alice)
        possessors[2] = bob
        ownership_test(scenario, c2, possessors)

        scenario.h4("Bob sends the same token to both Alice and itself (order)")
        c2.transfer([
                c2.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 2)
                                    ] + [
                                        sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 2)
                                    ])
            ]).run(sender = bob)
        possessors[2] = alice
        ownership_test(scenario, c2, possessors)

        scenario.h3("Invalid cases")

        scenario.h4("Alice sends 1 legit token and 1 non-existing token to Bob")
        c2.transfer([
                c2.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 2)
                                    ] + [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 1000)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c2, possessors)
        scenario.p("Transaction has been cancelled")

        scenario.h4("Alice sends 2 non-existing tokens to Bob")
        c2.transfer([
                c2.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 1000)
                                    ] + [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 1001)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c2, possessors)

        scenario.h4("Alice sends 2 times the same token to Bob")
        c2.transfer([
                c2.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 2)
                                    ] + [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 2)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c2, possessors)
        scenario.p("Transaction has been cancelled")

        scenario.h4("Alice sends the same token to both Bob and Admin")
        c2.transfer([
                c2.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 2)
                                    ] + [
                                        sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 2)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c2, possessors)
        scenario.p("Transaction has been cancelled")

        scenario.h4("Alice tries to force Bob to send 2 tokens to Admin")
        c2.transfer([
                c2.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 2)
                                    ] + [
                                        sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 2)
                                    ])
            ]).run(sender = alice, valid=False)
        ownership_test(scenario, c2, possessors)
        scenario.p("Transaction has been cancelled")


    @sp.add_test(name = "tzip12 tests operator", is_default = is_default)
    def tests_operator():
        scenario = sp.test_scenario()

        admin, [alice, bob] = get_addresses()

        config.max_editions = 10000
        c1 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)

        scenario.h1("Tests operator")

        scenario.table_of_contents()

        scenario.h2("Operator basic tests")

        scenario += c1

        scenario.p("Creates one operator")
        op = sp.test_account("Operator")

        scenario.p("Alice mints 3 tokens")
        c1.mint(3).run(sender = alice, amount = sp.mutez(3000000))
        possessors = [alice]*3

        scenario.h3("Operator tries to transfer Alice's token before being permitted to")

        c1.transfer([
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Alice grants Operator rights on token 0 and 2")

        c1.update_operators([
                sp.variant("add_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op.address,
                    token_id = 0)),
                sp.variant("add_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op.address,
                    token_id = 2))
            ]).run(sender = alice)

        scenario.h3("Operator transfers token 0 from Alice to Bob")

        c1.transfer([
        c1.batch_transfer.item(from_ = alice.address,
                            txs = [
                                sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op)
        possessors[0] = bob
        ownership_test(scenario, c1, possessors)

        scenario.h3("Operator tries to transfer token 0 from Bob to Alice")

        c1.transfer([
        c1.batch_transfer.item(from_ = bob.address,
                            txs = [
                                sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Alice transfers token 2 to Bob")

        c1.transfer([
        c1.batch_transfer.item(from_ = alice.address,
                            txs = [
                                sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 2)
                                    ])
            ]).run(sender = alice)
        possessors[2] = bob
        ownership_test(scenario, c1, possessors)

        scenario.h3("Operator is too late and tries to transfer token 2 to Admin")

        c1.transfer([
        c1.batch_transfer.item(from_ = alice.address,
                            txs = [
                                sp.record(to_ = admin.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op, valid=False)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Bob sends back its tokens to Alice")

        c1.transfer([
        c1.batch_transfer.item(from_ = bob.address,
                            txs = [
                                sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 0)
                                    ] + [
                                sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 2)
                                ])
            ]).run(sender = bob)
        possessors[0] = alice
        possessors[2] = alice
        ownership_test(scenario, c1, possessors)

        scenario.h3("Operator transfers again token 0 from Alice to Bob")

        c1.transfer([
        c1.batch_transfer.item(from_ = alice.address,
                            txs = [
                                sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op)
        possessors[0] = bob
        ownership_test(scenario, c1, possessors)

        scenario.h3("Bob gives Operator right to transfer its token 0")

        c1.update_operators([
            sp.variant("add_operator", c1.operator_param.make(
                owner = bob.address,
                operator = op.address,
                token_id = 0))
        ]).run(sender = bob)

        scenario.h3("Operator transfers token 0 from Bob to Alice")

        c1.transfer([
        c1.batch_transfer.item(from_ = bob.address,
                            txs = [
                                sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op)
        possessors[0] = alice
        ownership_test(scenario, c1, possessors)

        scenario.h2("Token loopback: does not cancels operator rights")

        scenario.h3("Alice grants Operator rights on token 0")

        c1.update_operators([
                sp.variant("add_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op.address,
                    token_id = 0))
            ]).run(sender = alice)

        scenario.h3("Alice transfers token 0 to itself")

        c1.transfer([
        c1.batch_transfer.item(from_ = alice.address,
                            txs = [
                                sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice)
        ownership_test(scenario, c1, possessors)

        scenario.h3("Operator still have rights to token 0") 
        c1.transfer([
        c1.batch_transfer.item(from_ = alice.address,
                            txs = [
                                sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op)
        possessors[0] = bob
        ownership_test(scenario, c1, possessors)

        scenario.h2("Naming operator on balance 0 token")

        config.max_editions = 10000
        c2 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)
        scenario += c2

        scenario.p("Alice mints 1 token")
        c2.mint(1).run(sender = alice, amount = sp.mutez(1000000))
        possessors = [alice]
        ownership_test(scenario, c2, possessors)

        scenario.h3("Bob names operator for token 0 he doesn't possess yet")

        c2.update_operators([
                sp.variant("add_operator", c2.operator_param.make(
                    owner = bob.address,
                    operator = op.address,
                    token_id = 0))
            ]).run(sender = bob)

        scenario.h3("Alice sends token 0 to Bob. Operator then has right on this token.")

        c2.transfer([
        c2.batch_transfer.item(from_ = alice.address,
                            txs = [
                                sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = alice)
        possessors[0] = bob
        ownership_test(scenario, c2, possessors)

        c2.transfer([
        c2.batch_transfer.item(from_ = bob.address,
                            txs = [
                                sp.record(to_ = alice.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op)
        possessors[0] = alice
        ownership_test(scenario, c2, possessors)

        scenario.h2("Granting in the name of someone else")

        scenario.h3("Admin tries to grant Operator rights on Alice's token 0")

        c2.update_operators([
                sp.variant("add_operator", c2.operator_param.make(
                    owner = alice.address,
                    operator = op.address,
                    token_id = 0))
            ]).run(sender = admin, valid=False)

        scenario.h3("Bob tries to grant Operator rights on Alice's token 0")

        c2.update_operators([
                sp.variant("add_operator", c2.operator_param.make(
                    owner = alice.address,
                    operator = op.address,
                    token_id = 0))
            ]).run(sender = bob, valid=False)

        scenario.h3("Alice itself cannot fake token owner in update_operators")

        c2.update_operators([
                sp.variant("add_operator", c2.operator_param.make(
                    owner = admin.address,
                    operator = op.address,
                    token_id = 0))
            ]).run(sender = alice, valid=False)

        scenario.h2("Multiple operators tests")

        op2 = sp.test_account("Operator#2")

        config.max_editions = 10000
        c3 = FA2(config = config,
            metadata = sp.utils.metadata_of_url("https://example.com"),
            admin = admin.address)
        scenario += c3

        scenario.p("Alice mints 3 token")
        c3.mint(3).run(sender = alice, amount = sp.mutez(3000000))

        scenario.p("Operator#1 mints a token")
        c3.mint(1).run(sender = op, amount = sp.mutez(1000000))

        possessors = [alice]*3 + [op]
        ownership_test(scenario, c3, possessors)

        scenario.p("Alice names Operator#1 as operator for token 0")

        c3.update_operators([
                sp.variant("add_operator", c3.operator_param.make(
                    owner = alice.address,
                    operator = op.address,
                    token_id = 0))
            ]).run(sender = alice)

        scenario.p("Operator#1 names Operator#2 as operator for non possessed token 0")

        c3.update_operators([
                sp.variant("add_operator", c3.operator_param.make(
                    owner = op.address,
                    operator = op2.address,
                    token_id = 0))
            ]).run(sender = op)

        scenario.h3("No operator transitivity: Operator#2 tries to smuggle token 0 of Alice via Operator#1")

        c3.transfer([
        c3.batch_transfer.item(from_ = alice.address,
                            txs = [
                                sp.record(to_ = bob.address,
                                                amount = 1,
                                                token_id = 0)
                                    ])
            ]).run(sender = op2, valid=False)
        ownership_test(scenario, c3, possessors)

        scenario.h3("Operator#1 cannot name Operator#2 as operator on Alice's token 0")

        c3.update_operators([
                sp.variant("add_operator", c3.operator_param.make(
                    owner = alice.address,
                    operator = op2.address,
                    token_id = 0))
            ]).run(sender = op, valid=False)

        scenario.h3("Alice can name two operators on the same token")

        c3.update_operators([
                sp.variant("add_operator", c3.operator_param.make(
                    owner = alice.address,
                    operator = op.address,
                    token_id = 1))
                , sp.variant("add_operator", c3.operator_param.make(
                    owner = alice.address,
                    operator = op2.address,
                    token_id = 1))
            ]).run(sender = alice)


        #     c1.update_operators([
        # sp.variant("remove_operator", c1.operator_param.make(
        #     owner = alice.address,
        #     operator = op1.address,
        #     token_id = 0)),

        return

        tok0_md = FA2.make_metadata(
            name = "The Token Zero",
            decimals = 2,
            symbol= "TK0" )
        c1.mint(address = alice.address,
                            amount = 50,
                            metadata = tok0_md,
                            token_id = 0).run(sender = admin)
        # Mint a second time
        c1.mint(address = alice.address,
                            amount = 50,
                            metadata = tok0_md,
                            token_id = 0).run(sender = admin)
        scenario.h2("Transfers Alice -> Bob")
        c1.transfer(
            [
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                  amount = 10,
                                                  token_id = 0)
                                    ])
            ]).run(sender = alice)
        scenario.verify(
            c1.data.ledger[c1.ledger_key.make(alice.address, 0)].balance == 90)
        scenario.verify(
            c1.data.ledger[c1.ledger_key.make(bob.address, 0)].balance == 10)
        c1.transfer(
            [
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                  amount = 10,
                                                  token_id = 0),
                                        sp.record(to_ = bob.address,
                                                  amount = 11,
                                                  token_id = 0)
                                    ])
            ]).run(sender = alice)
        scenario.verify(
            c1.data.ledger[c1.ledger_key.make(alice.address, 0)].balance == 90 - 10 - 11
        )
        scenario.verify(
            c1.data.ledger[c1.ledger_key.make(bob.address, 0)].balance
            == 10 + 10 + 11)
        scenario.h2("More Token Types")
        tok1_md = FA2.make_metadata(
            name = "The Second Token",
            decimals = 0,
            symbol= "TK1" )
        c1.mint(address = bob.address,
                            amount = 100,
                            metadata = tok1_md,
                            token_id = 1).run(sender = admin)
        tok2_md = FA2.make_metadata(
            name = "The Token Number Three",
            decimals = 0,
            symbol= "TK2" )
        c1.mint(address = bob.address,
                            amount = 200,
                            metadata = tok2_md,
                            token_id = 2).run(sender = admin)
        scenario.h3("Multi-token Transfer Bob -> Alice")
        c1.transfer(
            [
                c1.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                  amount = 10,
                                                  token_id = 0),
                                        sp.record(to_ = alice.address,
                                                  amount = 10,
                                                  token_id = 1)]),
                # We voluntarily test a different sub-batch:
                c1.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                  amount = 10,
                                                  token_id = 2)])
            ]).run(sender = bob)
        scenario.h2("Other Basic Permission Tests")
        scenario.h3("Bob cannot transfer Alice's tokens.")
        c1.transfer(
            [
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                  amount = 10,
                                                  token_id = 0),
                                        sp.record(to_ = bob.address,
                                                  amount = 1,
                                                  token_id = 0)])
            ]).run(sender = bob, valid = False)
        scenario.h3("Admin can transfer anything.")
        c1.transfer(
            [
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                  amount = 10,
                                                  token_id = 0),
                                        sp.record(to_ = bob.address,
                                                  amount = 10,
                                                  token_id = 1)]),
                c1.batch_transfer.item(from_ = bob.address,
                                    txs = [
                                        sp.record(to_ = alice.address,
                                                  amount = 11,
                                                  token_id = 0)])
            ]).run(sender = admin)
        scenario.h3("Even Admin cannot transfer too much.")
        c1.transfer(
            [
                c1.batch_transfer.item(from_ = alice.address,
                                    txs = [
                                        sp.record(to_ = bob.address,
                                                amount = 1000,
                                                token_id = 0)])
            ]).run(sender = admin, valid = False)
        scenario.h3("Consumer Contract for Callback Calls.")
        consumer = View_consumer(c1)
        scenario += consumer
        scenario.p("Consumer virtual address: "
                + consumer.address.export())



    @sp.add_test(name = config.name, is_default = is_default)
    def test():
        return
#ICICICICICICICI
#ICICICICICICICI
#ICICICICICICICI
#ICICICICICICICI
#ICICICICICICICI
#ICICICICICICICI
#ICICICICICICICI
#ICICICICICICICI
#ICICICICICICICI


        scenario.h2("Balance-of.")
        def arguments_for_balance_of(receiver, reqs):
            return (sp.record(
                callback = sp.contract(
                    Balance_of.response_type(),
                    receiver.address,
                    entry_point = "receive_balances").open_some(),
                requests = reqs))
        c1.balance_of(arguments_for_balance_of(consumer, [
            sp.record(owner = alice.address, token_id = 0),
            sp.record(owner = alice.address, token_id = 1),
            sp.record(owner = alice.address, token_id = 2)
        ]))
        scenario.verify(consumer.data.last_sum == 90)
        scenario.h2("Operators")
        if not c1.config.support_operator:
            scenario.h3("This version was compiled with no operator support")
            scenario.p("Calls should fail even for the administrator:")
            c1.update_operators([]).run(sender = admin, valid = False)
        else:
            scenario.p("This version was compiled with operator support.")
            scenario.p("Calling 0 updates should work:")
            c1.update_operators([]).run()
            scenario.h3("Operator Accounts")
            op0 = sp.test_account("Operator0")
            op1 = sp.test_account("Operator1")
            op2 = sp.test_account("Operator2")
            scenario.show([op0, op1, op2])
            scenario.p("Admin can change Alice's operator.")
            c1.update_operators([
                sp.variant("add_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op1.address,
                    token_id = 0)),
                sp.variant("add_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op1.address,
                    token_id = 2))
            ]).run(sender = admin)
            scenario.p("Operator1 can now transfer Alice's tokens 0 and 2")
            c1.transfer(
                [
                    c1.batch_transfer.item(from_ = alice.address,
                                        txs = [
                                            sp.record(to_ = bob.address,
                                                      amount = 2,
                                                      token_id = 0),
                                            sp.record(to_ = op1.address,
                                                      amount = 2,
                                                      token_id = 2)])
                ]).run(sender = op1)
            scenario.p("Operator1 cannot transfer Bob's tokens")
            c1.transfer(
                [
                    c1.batch_transfer.item(from_ = bob.address,
                                        txs = [
                                            sp.record(to_ = op1.address,
                                                      amount = 2,
                                                      token_id = 1)])
                ]).run(sender = op1, valid = False)
            scenario.p("Operator2 cannot transfer Alice's tokens")
            c1.transfer(
                [
                    c1.batch_transfer.item(from_ = alice.address,
                                        txs = [
                                            sp.record(to_ = bob.address,
                                                      amount = 2,
                                                      token_id = 1)])
                ]).run(sender = op2, valid = False)
            scenario.p("Alice can remove their operator")
            c1.update_operators([
                sp.variant("remove_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op1.address,
                    token_id = 0)),
                sp.variant("remove_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op1.address,
                    token_id = 0))
            ]).run(sender = alice)
            scenario.p("Operator1 cannot transfer Alice's tokens any more")
            c1.transfer(
                [
                    c1.batch_transfer.item(from_ = alice.address,
                                        txs = [
                                            sp.record(to_ = op1.address,
                                                      amount = 2,
                                                      token_id = 1)])
                ]).run(sender = op1, valid = False)
            scenario.p("Bob can add Operator0.")
            c1.update_operators([
                sp.variant("add_operator", c1.operator_param.make(
                    owner = bob.address,
                    operator = op0.address,
                    token_id = 0)),
                sp.variant("add_operator", c1.operator_param.make(
                    owner = bob.address,
                    operator = op0.address,
                    token_id = 1))
            ]).run(sender = bob)
            scenario.p("Operator0 can transfer Bob's tokens '0' and '1'")
            c1.transfer(
                [
                    c1.batch_transfer.item(from_ = bob.address,
                                        txs = [
                                            sp.record(to_ = alice.address,
                                                      amount = 1,
                                                      token_id = 0)]),
                    c1.batch_transfer.item(from_ = bob.address,
                                        txs = [
                                            sp.record(to_ = alice.address,
                                                      amount = 1,
                                                      token_id = 1)])
                ]).run(sender = op0)
            scenario.p("Bob cannot add Operator0 for Alice's tokens.")
            c1.update_operators([
                sp.variant("add_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op0.address,
                    token_id = 0
                ))
            ]).run(sender = bob, valid = False)
            scenario.p("Alice can also add Operator0 for their tokens 0.")
            c1.update_operators([
                sp.variant("add_operator", c1.operator_param.make(
                    owner = alice.address,
                    operator = op0.address,
                    token_id = 0
                ))
            ]).run(sender = alice, valid = True)
            scenario.p("Operator0 can now transfer Bob's and Alice's 0-tokens.")
            c1.transfer(
                [
                    c1.batch_transfer.item(from_ = bob.address,
                                        txs = [
                                            sp.record(to_ = alice.address,
                                                      amount = 1,
                                                      token_id = 0)]),
                    c1.batch_transfer.item(from_ = alice.address,
                                        txs = [
                                            sp.record(to_ = bob.address,
                                                      amount = 1,
                                                      token_id = 0)])
                ]).run(sender = op0)
            scenario.p("Bob adds Operator2 as second operator for 0-tokens.")
            c1.update_operators([
                sp.variant("add_operator", c1.operator_param.make(
                    owner = bob.address,
                    operator = op2.address,
                    token_id = 0
                ))
            ]).run(sender = bob, valid = True)
            scenario.p("Operator0 and Operator2 can transfer Bob's 0-tokens.")
            c1.transfer(
                [
                    c1.batch_transfer.item(from_ = bob.address,
                                        txs = [
                                            sp.record(to_ = alice.address,
                                                      amount = 1,
                                                      token_id = 0)])
                ]).run(sender = op0)
            c1.transfer(
                [
                    c1.batch_transfer.item(from_ = bob.address,
                                        txs = [
                                            sp.record(to_ = alice.address,
                                                      amount = 1,
                                                      token_id = 0)])
                ]).run(sender = op2)
            scenario.table_of_contents()

##
## ## Global Environment Parameters
##
## The build system communicates with the python script through
## environment variables.
## The function `environment_config` creates an `FA2_config` given the
## presence and values of a few environment variables.
def global_parameter(env_var, default):
    try:
        if os.environ[env_var] == "true" :
            return True
        if os.environ[env_var] == "false" :
            return False
        return default
    except:
        return default

def environment_config():
    return FA2_config(
        debug_mode = global_parameter("debug_mode", False),
        non_fungible = global_parameter("non_fungible", False),
        readable = global_parameter("readable", True),
        force_layouts = global_parameter("force_layouts", True),
        support_operator = global_parameter("support_operator", True),
        store_total_supply = global_parameter("store_total_supply", False),
        allow_self_transfer = global_parameter("allow_self_transfer", False),
        max_editions = global_parameter("max_editions", 2),
    )

## ## Standard “main”
##
## This specific main uses the relative new feature of non-default tests
## for the browser version.
if "templates" not in __name__:
    add_test(environment_config())

    sp.add_compilation_target("FA2_comp", FA2(config = environment_config(),
                              metadata = sp.utils.metadata_of_url("https://example.com"),
                              admin = sp.address("tz1M9CMEtsXm3QxA7FmMU2Qh7xzsuGXVbcDr")))
