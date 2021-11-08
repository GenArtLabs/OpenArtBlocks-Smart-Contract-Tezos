def run_tests_set_mint_parameters(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()
    
    scenario.h1("Tests set mint parameters")
    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Admin sets mint parameters\nMint price is properly updated")

    contract = create_new_contract(config, admin, scenario, [])

    scenario.p("Admin cannot mint for 1 mutez")

    contract.mint(1).run(sender=admin, amount=sp.mutez(1), valid=False)

    scenario.p("Admin sets mint price to 1 mutez")

    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1)
    ).run(sender=admin)

    scenario.p("Admin now can mint for 1 mutez")  

    contract.mint(1).run(sender=admin, amount=sp.mutez(1))

    ownership_test(scenario, contract, [admin])

    #-----------------------------------------------------
    scenario.h2("Admin sets mint parameters\nMax editions is properly updated")

    contract = create_new_contract(config, admin, scenario, [])

    scenario.p("Admin sets max editions to 1")

    contract.set_mint_parameters(
        max_editions=1, price=sp.mutez(1000000)
    ).run(sender=admin)

    scenario.p("Admin cannot mint more than 1 token")  

    contract.mint(2).run(sender=admin, amount=sp.mutez(2000000), valid=False)

    #-----------------------------------------------------
    scenario.h2("Alice tries to set mint price to 1 mutez")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1)
    ).run(sender=alice, valid=False)

    scenario.p("Mint price is still to 1000000 mutez")

    contract.mint(1).run(sender=alice, amount=sp.mutez(1), valid=False)

    #-----------------------------------------------------
    scenario.h2("Mint parameters can be updated several times")

    possessors = [admin]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("First update")
    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1000000)
    ).run(sender=admin)

    scenario.p("Cannot mint for 1 mutez")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1), valid=False)

    scenario.p("Second update")
    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1)
    ).run(sender=admin)

    scenario.p("Can now mint for 1 mutez")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1))

    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Mint parameters can be updated after 1 mint")

    possessors = [admin]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Update is still possible")
    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1)
    ).run(sender=admin)

    scenario.p("Can now mint for 1 mutez")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1))

    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Mint parameters cannot be updated after 2 mint")

    possessors = [admin]*2
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Update not possible anymore")
    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1)
    ).run(sender=admin, valid=False)

    scenario.p("Cannot mint for 1 mutez")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1), valid=False)

    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("1 mint, update, 1 mint, update not possible")

    possessors = [admin]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Update is still possible")
    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1)
    ).run(sender=admin)

    scenario.p("Can now mint for 1 mutez")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1))

    scenario.p("Update not possible anymore")
    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1000000)
    ).run(sender=admin, valid=False)

    scenario.p("Price is still 1 mutez")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1))

    ownership_test(scenario, contract, [admin]*3)

    #-----------------------------------------------------
    scenario.h2("Can downgrade max editions to 0 if nothing is minted")

    contract = create_new_contract(config, admin, scenario, [])

    scenario.p("Update max editions to 0")
    contract.set_mint_parameters(
        max_editions=0, price=sp.mutez(1)
    ).run(sender=admin)

    scenario.p("Cannot mint")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1), valid=False)

    scenario.p("Update max editions to 1024 again")
    contract.set_mint_parameters(
        max_editions=1024, price=sp.mutez(1)
    ).run(sender=admin)

    scenario.p("Can now mint")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1))

    ownership_test(scenario, contract, [admin])

     #-----------------------------------------------------
    scenario.h2("Can downgrade max editions to 0 if a token is minted")

    contract = create_new_contract(config, admin, scenario, [admin])

    scenario.p("Update max editions to 0 is not possible")
    contract.set_mint_parameters(
        max_editions=0, price=sp.mutez(1)
    ).run(sender=admin, valid=False)

    scenario.p("Can still mint")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1000000))

    ownership_test(scenario, contract, [admin]*2)
