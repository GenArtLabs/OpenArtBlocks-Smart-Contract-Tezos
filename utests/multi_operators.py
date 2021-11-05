def run_tests_multi_operators(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    config.max_editions = 10000

    scenario.h1("Multiple operators tests")

    scenario.table_of_contents()

    op = sp.test_account("Operator#1")
    op2 = sp.test_account("Operator#2")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    #-----------------------------------------------------
    scenario.h2("No transitivity between operators")

    scenario.p("Alice names Operator#1 as operator for token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.p("Operator#1 names Operator#2 as operator for non possessed token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=op.address,
            operator=op2.address,
            token_id=0))
    ]).run(sender=op)

    scenario.h3(
        "No operator transitivity: Operator#2 tries to smuggle token 0 of Alice via Operator#1")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op2, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "Operator cannot name another operator for a granted token"
        "(No transitivity for token granting)"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Alice grants Operator#1 on token 0")
    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.h3("Operator#1 cannot name Operator#2 as operator on Alice's token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op2.address,
            token_id=0))
    ]).run(sender=op, valid=False)

    #-----------------------------------------------------
    scenario.h2("Alice can name two operators on the same token")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=1)),
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op2.address,
            token_id=1))
    ]).run(sender=alice)

    #-----------------------------------------------------
    scenario.h2("Alice grants access to 2 tokens to the same operator")

    possessors = [alice]*2
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0)),
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=1))
    ]).run(sender=alice)

    scenario.h3("Operator can transfer both tokens")
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
    ]).run(sender=op)
    possessors = [bob]*2
    ownership_test(scenario, contract, possessors)
