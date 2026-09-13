# WAN Synthesizer

WAN Synthesizer is a web application that synthesizes a **2-vertex-connected** wide area network for a tenant: the loss of any one carrier PoP the WAN runs through leaves every remaining PoP on it still reaching every other. Equivalently, between every pair of PoPs the WAN runs through, two circuits run that share no intermediate PoP.

A tenant's inputs are its sites — named places with a coordinate — the provider regions it reaches, and the carrier PoPs and fiber segments on offer. The synthesizer selects carrier PoPs as the WAN PoPs, homes each site and each provider region into them, and joins the WAN PoPs with circuits; a circuit runs from one place to another over the fiber segments a carrier offers, through whatever transit PoPs lie between. Every PoP the WAN runs through is held to the guarantee above, the WAN PoPs a tenant's inputs select and the transit PoPs its circuits pass through alike.

The application accepts the inputs over an API, publishes the WAN beside the fiber miles it runs over and the fewest miles the same requirements could have been met with, and renders it as a webpage.
