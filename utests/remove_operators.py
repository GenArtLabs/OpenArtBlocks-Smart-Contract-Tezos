def run_tests_remove_operator(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()
    op = sp.test_account("Operator#1")
    op2 = sp.test_account("Operator#2")

    config.max_editions = 10000

    scenario.h1("Removing operator tests")

    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Removing non-added operator")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    #-----------------------------------------------------
    scenario.h2("Removing non-added operator on non-possessed token")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=bob)

    #-----------------------------------------------------
    scenario.h2("Removing non-added operator on non-existing token")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=1000)),
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Removing someone else non-added operator")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=bob, valid=False)

    #-----------------------------------------------------
    scenario.h2("Removing someone else added operator")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=bob, valid=False)

    scenario.h3("Non-removed operator should still be able to transfer alice's token")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Removing someone else operator on non-existing token")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=1000)),
    ]).run(sender=bob, valid=False)

    #-----------------------------------------------------
    scenario.h2("Removed operator has no right on token anymore")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    scenario.h3("Removed operator tries to transfer Alice's token 0")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Operator granted on multiple token, then removed on one token cannot smuggle that token")

    possessors = [alice]*2
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ] + [
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=1))

    ]).run(sender=alice)

    scenario.p("Alice removes operator on token 0")

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    scenario.h3("Operator tries to smuggle both tokens at once")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ] + [
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Operator transfers a token, loses rights, then gets back the token and tries to smuggle it")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.p("Operator sends token to bob")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    scenario.p("Alice removes operator")

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    scenario.p("Bob sends back token to Alice")

    contract.transfer([
        contract.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=bob)
    possessors[0] = alice
    ownership_test(scenario, contract, possessors)

    scenario.h3("Removed operator tries to transfer Alice's token 0")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "Two operators on the same tokens\n"
        "If one operator is removed, the other can still stransfer the token"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Alice adds two different operators on the same token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ], [
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op2.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.h3("Alice removes Operator#1 on this token 0")

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
    ]).run(sender=alice)

    scenario.h3("Operator#2 still can smuggle token 0")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op2)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "update_operators commands order tests:\n"
        "Alice adds THEN removes Operator#1 during the same request"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ], [
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.h3("Operator#1 should not be able to smuggle Alice's token 0")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "update_operators commands order tests:\n"
        "Alice removes THEN add Operator#1 during the same request"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ], [
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.h3("Operator#1 should be able to smuggle Alice's token 0")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "If one of sub command of update_operators is invalid, whole transaction is canceled\n"
        "Wrong remove, good add"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.h3("Alice makes invalid add request")

    contract.update_operators([
        sp.variant("remove_operator", contract.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ], [
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice, valid=False)

    scenario.h3("Operator#1 should not be able to smuggle Alice's token 0")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)
