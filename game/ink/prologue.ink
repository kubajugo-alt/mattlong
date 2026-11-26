// =====================================================================================================
// MATT LONG: THE BLOODY ANGLE
// Prologue, "Rent Day". Thursday 20 November 1930. First snow; rain by night.
// First draft for review (26 Nov 2026). Source: docs/bible + docs/decisions.md.
//
// HOW TO READ THIS FILE
//   SPEAKER: line        spoken aloud (MATT, PETE, KATE, LEE, SOL, JUNKIE, INEZ, NEWSBOY)
//   VO: line             Matt's voice-over (narration, right-click descriptions)
//   * [choice]           a dialogue choice the player picks; text in [] is shown, not spoken
//   ~ act("...")         an instruction for the engine (see ENGINE CONTRACT at the bottom)
//   // comment           notes for us; never shown in the game
//
// HOW THE ENGINE CALLS IT
//   <room>__<hotspot>.look   right-click / long-press on a hotspot (hotspot ids from the room data, - becomes _)
//   <room>__<hotspot>.use    left-click / tap
//   <room>__<hotspot>.talk   left-click on a person
//   <room>__<hotspot>.<item> an inventory item used on the hotspot (e.g. alley__junkie.cigarettes)
//   item__<item>.look        right-click on an inventory item
//   Missing stitch -> the room's __default fallback lines.
// =====================================================================================================

VAR read_notice = false        // P1 gate: the notice is read, Matt can leave the office
VAR heard_book = false         // Pete told him about Lee's stolen account book
VAR has_cigs = false
VAR kate_gone = false          // Kate leaves for work once Matt has the cigarettes
VAR met_lee = false            // Lee asked Matt to bring the book back
VAR sol_refused = false        // Sol wants the ticket
VAR has_ticket = false
VAR has_book = false
VAR book_returned = false      // P4 done: two weeks' grace
VAR case_taken = false         // P5 done
VAR told_lee_where = false     // small, untracked choice in P4
VAR has_cup = false          // Matt took the spare cup off Kate's table (coffee needs a cup)
VAR had_coffee = false
VAR radio_on = false         // the office radio is playing
VAR mask = 0                   // The Mask: +1 honest, -1 guarded (bible: feeds 3.1, 3.2, the epilogue)

EXTERNAL act(command)   // engine actions: "give:cigarettes", "go:corridor", ... (see ENGINE CONTRACT)

-> prologue_start

=== prologue_start ===
~ act("card:prologue")
// Title card: PROLOGUE / RENT DAY / Doyers Street · Thursday, 20 November 1930
~ act("scene:office-day")
~ act("anim:matt:wake_at_desk")
VO: Thursday. The first snow of the year was coming down on Doyers Street like it hadn't been told about the Depression.
VO: I'd slept at the desk again. The desk didn't mind. The desk was paid for.
-> DONE


// =====================================================================================================
// P1 · MATT'S OFFICE, MORNING
// Teaches: look (right-click / long-press), walking, hotspot highlight (torch). Gate: read the notice.
// =====================================================================================================

=== office__default ===
= look
{~VO: Nothing there but dust, and the dust is mine.|VO: Seen it. Didn't help then either.|VO: If that was a clue, I'd have spotted it years ago.}
-> DONE
= use
{~VO: No.|VO: It's fine where it is.|VO: I've got bigger problems than that.}
-> DONE

=== office__eviction_notice ===
= look
VO: An envelope, pushed under the door. Nobody slides good news under a door.
-> DONE
= use
~ read_notice = true
~ act("give:eviction-notice")
~ act("hide:eviction-notice")
~ act("sfx:paper")
VO: Love letter from the landlord. He always writes when the money's late.
VO: Fifty dollars by Saturday, or "vacate the premises". Lee Wing writes a nice formal English when he's annoyed.
VO: Fifty dollars. I had a dollar and change, a hat, and a talent for finding things other people had lost.
VO: Pete would know who'd lost something this week. Pete always knows.
-> DONE

=== office__door ===
= look
VO: M. LONG, INVESTIGATIONS. Painted backwards from in here, like most of my life.
-> DONE
= use
{read_notice:
    ~ act("go:corridor")
    -> DONE
- else:
    VO: Somebody's slid something under it. Somebody wants it read before I go.
    -> DONE
}

=== office__desk ===
= look
VO: My desk. Most of my clients have only ever seen the front of it.
-> DONE
= use
~ act("sfx:drawer")
VO: Top drawer: string, a broken pencil, and Natalia.
VO: Her photo, face-down, the way I keep it. Some cases you close. Some you just stop looking at.
-> DONE

=== office__whiskey_bottle ===
= look
VO: Empty. The bottle, I mean. The day's still got some fight in it.
-> DONE
= use
VO: I shook it, in case it had changed its mind. It hadn't.
-> DONE

=== office__window ===
= look
VO: The Bloody Angle. Tong men used to shoot each other round that bend. Now it's mostly laundry.
VO: First snow. By noon it'd be grey slush, same as everything else on this street.
-> DONE

=== office__window_blinds ===
= look
VO: The blinds cut the morning into strips. It's easier to take that way.
-> DONE

=== office__radio ===
= look
VO: The radio. Dance bands in the morning, bad news by night.
-> DONE
= use
// the radio really plays: WMCA's bulletins and records (game/radio/broadcast.json), from the set, until switched off
{radio_on:
    ~ radio_on = false
    ~ act("radio:off")
    {~VO: Off. The bad news can wait. It always does.|VO: Quiet. The city can tell me the rest tomorrow.}
- else:
    ~ radio_on = true
    ~ act("radio:on")
    {once:
    - VO: WMCA, from the roof of the Hotel McAlpin. The news, and records older than my debts.
    - VO: A dance band, playing like nobody had told them about the bread lines either.
    - VO: The radio. Company that doesn't ask for a retainer.
    }
}
-> DONE

=== office__evidence_board ===
= look
VO: Old cases. String and photographs. Every one of them paid less than it cost.
-> DONE
= use
VO: Nothing new to pin up. That's the trouble with nothing new.
-> DONE

=== office__framed_certificate_1 ===
= look
VO: An NYPD commendation, 1924. They give you a frame while you're useful.
-> DONE

=== office__framed_diploma ===
= look
VO: A licence to investigate, issued by the State of New York. It doesn't say what.
-> DONE

=== office__telephone ===
= look
VO: The telephone. The phone company and I aren't speaking.
-> DONE
= use
VO: Dead. Same as my credit.
-> DONE

=== office__sofa ===
= look
VO: The sofa. A client's chair when there are clients. My bed when there aren't.
-> DONE

=== office__radiator ===
= look
VO: The radiator knocks twice a day. It's the only thing in here that works for nothing.
-> DONE

=== office__floor_stain ===
= look
VO: Coffee. Mostly.
-> DONE

=== office__hat_on_hook ===
= look
VO: The spare hat. In my line you go through hats.
-> DONE

=== office__trench_coat ===
= look
VO: My good coat. It's the one with the lining.
-> DONE

=== office__ashtray ===
= look
VO: Butts, no cigarettes. Story of my week.
-> DONE

=== office__filing_cabinet ===
= look
VO: Closed cases, open bills. The cabinet doesn't care which drawer is which.
-> DONE
= use
~ act("sfx:drawer")
VO: Unpaid invoices, filed under "optimism".
-> DONE

=== office__paper_on_window_sill ===
= look
VO: A note to myself: "Pay the rent." I've been meaning to read it.
-> DONE

=== office__light_switch ===
= use
~ act("sfx:switch")
VO: The bulb thought about it and decided against.
-> DONE


// =====================================================================================================
// FIRST-FLOOR CORRIDOR
// =====================================================================================================

=== corridor__default ===
= look
{~VO: Brown paint over green paint over a hundred years of tenants.|VO: The building creaks. It's been holding its breath since 1890.}
-> DONE
= use
VO: That's not mine to touch.
-> DONE

=== corridor__flat_door ===
= look
VO: Pete and Kate's place. You can hear the percolator from here, and Pete over the percolator.
-> DONE
= use
~ act("go:pete-kate-flat")
~ act("sfx:door")
-> DONE

=== corridor__office_door ===
= look
VO: Number twelve. My office, my bedroom, my address for another two days.
-> DONE
= use
{book_returned and not case_taken:
    -> p5_evening
- else:
    VO: Nothing in there but the rent I don't have.
    -> DONE
}

=== corridor__street_door_below ===
= look
VO: The stairs down to Doyers Street. Forty-one of them. I've counted, on bad nights.
-> DONE
= use
{heard_book:
    ~ act("go:doyers-street")
    -> DONE
- else:
    VO: Not yet. Pete hears things before the police do. I'll start next door.
    -> DONE
}

=== corridor__newspaper ===
= look
VO: The Evening Clarion. Pete brings it home every night and reads his own byline like it's a love letter.
-> DONE

=== corridor__milk_bottle ===
= look
VO: Somebody's milk. In this building, that's practically a safe deposit.
-> DONE

=== corridor__bulb ===
= look
VO: One bare bulb for the whole landing. Lee Wing believes in thrift. Other people's.
-> DONE


// =====================================================================================================
// P2 · PETE & KATE'S FLAT
// Teaches: dialogue tree; the first small Mask line; "Pete knows and doesn't care". Gate: Pete's cigarettes.
// Kate sits at the kitchen table, Pete backwards on his desk chair.
// =====================================================================================================

=== flat_enter ===
// played once, the first time Matt walks in
PETE: Coffee's on me. Technically it's on Kate. Don't tell Kate.
KATE: Kate can hear you, Peter. Kate is four feet away.
VO: The coffee was Kate's, the hangover was Pete's, and I'd brought my own.
-> DONE

=== flat__default ===
= look
{~VO: Pete's mess on one side, Kate's order on the other. The border's under constant negotiation.|VO: Everything in here's either filed or on the floor.}
-> DONE
= use
VO: Kate would know. Kate always knows.
-> DONE

=== flat__percolator ===
= look
VO: The percolator. The hardest-working thing in this flat, and that includes Kate.
-> DONE
= use
{had_coffee:
    VO: One cup is hospitality. Two is a loan.
- else:
    {has_cup:
        VO: I had Kate's cup in my pocket. All it needed was to go under the spout.
    - else:
        VO: I'd need a cup. There's a clean one on the table. Kate lays one out for whoever turns up. Usually it's me.
    }
}
-> DONE
= coffee_cup
~ act("sfx:pour")
~ act("take:coffee-cup")
~ has_cup = false
~ had_coffee = true
VO: I poured myself a cup. It tasted like somebody else's rent money.
-> DONE

=== flat__teacup_3 ===
= look
VO: A clean cup on a saucer, set out for whoever turns up. Usually it's me.
-> DONE
= use
~ act("hide:teacup-kate")
~ act("hide:teacup-empty")
~ act("hide:teacup-3")
~ act("give:coffee-cup")
~ has_cup = true
{kate_gone:
    VO: I took the cup. Kate would know. Kate always knows.
- else:
    KATE: It's clean, Matt. Bring it back that way.
}
-> DONE

=== flat__newspaper_on_table ===
// Pete's paper, today's edition. A different story each time Matt picks it up: the real New York of November 1930.
= look
VO: Today's Clarion, folded to Pete's page. Kate reads it from the front, Pete from his own byline.
-> DONE
= use
{cycle:
    - VO: "Crater Still Missing." A Supreme Court justice hails a cab on West Forty-Fifth Street in August and is never seen again. Three months, and the police have a reward poster and a shrug.
    - VO: "Seabury Widens Magistrates' Inquiry." Talk of vice cops framing women in the Women's Court, and bondsmen splitting the bail. Somewhere in this city, a detective is wondering if his name comes up next.
    - VO: "Apple Sellers on Every Corner." The growers' association sells them a crate on credit, and they sell the apples at a nickel each. Six thousand men with a box and a tie. I counted two of them on my block who used to be bankers.
    - VO: "Roosevelt Re-Elected by Record Margin." The governor wins by seven hundred thousand votes. Tammany is pleased. When Tammany is pleased, somebody else is paying.
    - VO: "Legs Diamond Will Live, Doctors Say." Shot five times at the Hotel Monticello last month, and still breathing. They haven't made the bullet that can find his heart. Nobody's sure he has one.
    - VO: "Mooring Mast Rises Atop Empire State." A dock for airships, a quarter of a mile above Fifth Avenue. The city can't pay its rent, but it can build a ladder to heaven.
    - VO: "Half a Million Out of Work in City." The Prosser committee asks everyone with a job to give a day's pay. Most people I know haven't had a day's pay to give since summer.
}
-> DONE

=== item__coffee_cup ===
= look
VO: Kate's spare cup. Good china, meaning it hasn't broken yet.
-> DONE

=== flat__petes_cigarettes ===
= look
VO: Pete's cigarettes. Right there on the table, where Kate can watch them.
-> DONE
= use
{kate_gone or has_cigs:
    VO: Already in my pocket.
- else:
    KATE: Don't.
    VO: She didn't even look up.
}
-> DONE

=== flat__typewriter ===
= look
VO: Pete's typewriter. He's got his back to it. That's how Pete writes: facing the room, in case something happens.
-> DONE

=== flat__petes_clippings ===
= look
VO: Pete's clippings. Every crime on the Lower East Side since 1927, and a few he only hoped for.
-> DONE

=== flat__kates_ledgers ===
= look
VO: Kate's ledgers. Neat columns. Kate's the only person I know whose sums come out the same twice.
-> DONE

=== flat__bookcase ===
= look
VO: Kate's bookcase. Arranged by subject. Pete's books are arranged by where he dropped them.
-> DONE

=== flat__photo_by_the_clippings ===
= look
VO: Pete and Kate on their wedding day. Pete's grinning like he got away with something. He did.
-> DONE

=== flat__window ===
= look
VO: The air shaft. Pete calls it "the view". Pete calls a lot of things a lot of things.
-> DONE

=== flat__front_door ===
= use
~ act("go:corridor")
~ act("sfx:door")
-> DONE

// ---- PETE ---------------------------------------------------------------------------------------------

=== flat__pete ===
= look
VO: Pete Duckerton, crime reporter. Thirty-five going on fifteen. Hat on the back of his head, even indoors.
-> DONE
= cigarettes
VO: Giving Pete back his own cigarettes would be the most honest thing I'd done all week. And the least useful.
-> DONE
= talk
-> pete_hub

=== pete_hub ===
{kate_gone and not pete_last_night: -> pete_last_night}
* [Anything in the paper?] -> pete_news
* {heard_book} [Who'd steal a book of names?] -> pete_who
* {heard_book and not has_cigs} [Spare a smoke, Pete?] -> pete_smoke
* [How's the Clarion treating you?] -> pete_clarion
+ [See you later.]
    PETE: Not if I see you first. That's journalism.
    -> DONE

= pete_news
PETE: Depends. You want the news, or the news they let me print?
MATT: The second one. I'm short on time.
PETE: Somebody turned over Lee Wing's tea house Tuesday night. Didn't touch the till. Took his account book.
MATT: His account book.
PETE: Thirty years of who owes Lee Wing what. In Chinatown, that's not a book. That's a map.
~ heard_book = true
~ act("journal:lee-book")
VO: Lee Wing owned the tea house, two tenements on Doyers Street, mine included, and my overdue rent. A man who got his book back might forget a few dollars.
VO: Might.
PETE: Tong business, mark my words. "Blood on Doyers Street." I can see the headline.
KATE: Pete, a story isn't true because it's exciting. It's true because it adds up.
PETE: That's why I married her. Somebody's got to do the arithmetic.
-> pete_hub

= pete_who
PETE: Somebody who can't read Chinese and thought it looked expensive. Brass clasp. Nice cloth.
PETE: A thing like that ends up on the Bowery by breakfast. Sol Abramowitz takes anything with a hinge.
MATT: And Sol takes it in exchange for a ticket.
PETE: And forgets the face. Sol's got a memory like a sieve, and it's a very expensive sieve.
-> pete_hub

= pete_smoke
PETE: Love to. Can't. Kate's rationing me.
PETE: One pack a week, left on the table where I can see it. It's psychological warfare, Matt.
KATE: It's arithmetic, Peter.
VO: If I was going to the Bowery broke, I needed something to trade. On the Bowery, cigarettes are money that burns.
-> pete_hub

= pete_clarion
PETE: Clarion's cutting staff. Every week another desk goes quiet. I'm writing twice as much so they can't hear mine.
PETE: And there's a fella on the Bowery who thinks I owe him money.
MATT: Do you?
PETE: It's a matter of interpretation.
// Pete's debt to Nicky "Two Dimes" (Brancato's bookie) pays off in later acts; no names here.
-> pete_hub

= pete_last_night
// After Kate has left for work. The first small Mask line, and the beat where Pete knows and doesn't care.
PETE: So. You walked out on the Clarion wake before the second bottle. Where'd you get to?
* [Walked. Thought. Came home. #mask:guarded]
    ~ mask -= 1
    MATT: Walked. Thought. Came home.
    PETE: All three? In one night? You'll strain something.
    VO: Pete let it go. Pete always lets it go. That's what makes him dangerous to lie to.
* [A place in the Village. There was a piano player. #mask:honest]
    ~ mask += 1
    MATT: A place in the Village. There was a piano player.
    PETE: Yeah? Any good?
    MATT: He was good.
    PETE: Then go back and tell him so. Life's short, and the rent's due either way.
    VO: Pete's known for years. He's never once made it a thing. It's the one room in New York where I take my hat off.
- -> pete_hub

// ---- KATE ---------------------------------------------------------------------------------------------

=== flat__kate ===
= look
VO: Kate Duckerton. Accountant. The only person in this building who knows what day it is and what it costs.
-> DONE
= cigarettes
KATE: Don't wave those at me, Matthew. They're evidence.
-> DONE
= talk
-> kate_hub

=== kate_hub ===
* [Big day at the office?] -> kate_work
* {heard_book and not has_cigs} [About Pete's cigarettes...] -> kate_cigs
+ [I'll leave you to it.]
    KATE: You always do. Drink your coffee first, it's paid for.
    -> DONE

= kate_work
KATE: Head of accounts, if the board can bring themselves to say "Mrs." in a meeting. They're practising.
MATT: First woman to run the numbers.
KATE: First woman to be blamed for them. I'm under no illusions.
// Kate's secret (the books that don't add up at Halcyon) is not touched in the Prologue.
-> kate_hub

= kate_cigs
KATE: No.
MATT: I haven't asked yet.
KATE: You were going to. You have your asking face on.
-> kate_cigs_ask

= kate_cigs_ask
* [It's for a good cause. Mine.]
    MATT: It's for a good cause. Mine.
    KATE: That's not a cause, Matthew. That's a symptom.
    -> kate_cigs_ask
* [Pete wants to quit anyway.]
    MATT: Pete wants to quit anyway.
    PETE: I want a lot of things.
    KATE: He does. It's his most consistent quality.
    -> kate_cigs_ask
* [Think of it as an investment.]
    MATT: Think of it as an investment. I trade the smokes for Lee Wing's book, Lee forgets the rent, you keep your neighbour.
    KATE: ...
    KATE: Sound reasoning. Badly dressed, but sound.
    ~ has_cigs = true
    ~ act("give:cigarettes")
    ~ act("hide:petes-cigarettes")
    KATE: Pete, that was this week's.
    PETE: This is a hostage situation.
    KATE: And I'm late. Some of us work with facts.
    ~ kate_gone = true
    ~ act("anim:kate:stand")
    ~ act("hide:kate-at-table")
    ~ act("sfx:door")
    // Kate leaves for work: the table set stays, Kate's sprite goes (needs an empty-chair version of the table set).
    VO: Kate left. The flat got bigger and less sensible.
    -> DONE
+ [Never mind.]
    KATE: I'll be here. Not giving you Pete's cigarettes.
    -> DONE


// =====================================================================================================
// P3 · DOYERS STREET, THE PAWNSHOP, THE ALLEY
// Teaches: inventory, give / use. Trade Pete's cigarettes to the junkie for the ticket; ticket to Sol for the book.
// =====================================================================================================

=== doyers__default ===
= look
{~VO: Doyers Street. One bend, three hundred feet, and a reputation it earned the hard way.|VO: Laundry, lanterns and steam. Chinatown keeps its secrets warm.}
-> DONE
= use
VO: Better leave that where it is. Things on this street belong to somebody.
-> DONE

=== doyers__apartment_door ===
= use
~ act("go:corridor")
~ act("sfx:door")
-> DONE

=== doyers__tea_house_doors ===
= look
VO: Lee Wing's tea house. Lee owns it, the tenement across the street where I live, and one more besides. And my rent.
-> DONE
= use
~ act("go:tea-house")
~ act("sfx:door")
-> DONE

=== doyers__pawnbrokers_balls ===
= look
VO: Three brass balls. Two to one you won't get it back.
-> DONE

=== doyers__pawnshop_window ===
= look
VO: Other people's lives in a window, at a reasonable rate of interest.
-> DONE

=== doyers__newsboy ===
= look
VO: The kid sells the Clarion on this corner every morning. Pete tips him a nickel to shout his headlines louder.
-> DONE
= talk
NEWSBOY: Paper, mister? Two cents!
MATT: I've got a friend who writes it. I get it for free and it still costs me.
NEWSBOY: Then you owe me two cents for the joke.
-> DONE

=== doyers__far_street_lamp ===
= look
VO: The far end opens onto the Bowery and the rest of the city. The rest of the city can wait until I can afford it.
-> DONE

=== doyers__washing ===
= look
VO: Somebody's long johns, frozen stiff. It's going to be that kind of winter.
-> DONE

// ---- LEE WING (P3 visit: he asks for the book) -------------------------------------------------------

=== tea__default ===
= look
{~VO: Lacquer, smoke and an abacus that never stops counting.|VO: Lee Wing's tea house. Quiet as a church, if a church kept accounts.}
-> DONE
= use
VO: Lee's things stay where Lee puts them.
-> DONE

=== tea__lee_wing ===
= look
VO: Lee Wing. My landlord. He knows what everybody on Doyers Street owes, to the penny and the favour.
-> DONE
= talk
{book_returned: -> lee_after}
{has_book: -> lee_return}
{met_lee: -> lee_reminder}
-> lee_first

= account_book
-> lee_return

= cigarettes
LEE: I don't smoke, Mr. Long. It shortens the memory.
-> DONE

=== lee_first ===
~ met_lee = true
LEE: Mr. Long. You read my letter.
MATT: Beautiful penmanship. I was moved.
LEE: Fifty dollars moves me also.
LEE: Mr. Long. Someone has taken my account book. Thirty years of names. I would like it back... before anybody reads it.
MATT: You want me to find it.
LEE: I want it on my counter. How it gets there is your business. You have a business, I think. It says so on your door.
* [And the rent?]
    MATT: And the rent?
    LEE: Bring the book, and the rent can wait two weeks.
* [What's in it for me?]
    MATT: What's in it for me?
    LEE: A roof. It is snowing, Mr. Long.
- LEE: A boy was seen running toward the Bowery. Thin. A coat too big for him.
LEE: Ah Ming! Cha!
// Lee calls to the back room in Cantonese for tea ("cha"); bible: Cantonese for Lee's lines to staff.
~ act("journal:find-book")
VO: A thin boy, a big coat, and the Bowery. That narrowed it down to half the Bowery.
-> DONE

=== lee_reminder ===
LEE: The book, Mr. Long. My counter. Two weeks.
-> DONE

// ---- SOL ABRAMOWITZ ----------------------------------------------------------------------------------

=== pawn__default ===
= look
{~VO: Cages of other people's lives, and a dim bulb to read the price by.|VO: Every object in here was somebody's last good idea.}
-> DONE
= use
SOL: You break it, you bought it. You look at it, I'm watching.
-> DONE

=== pawn__front_door ===
= use
~ act("go:doyers-street")
~ act("sfx:shop-bell")
-> DONE

=== pawn__back_door ===
= look
VO: The back door. Out to the alley, where the Bowery keeps what it doesn't want seen.
-> DONE
= use
~ act("go:alley")
~ act("sfx:door")
-> DONE

=== pawn__sols_ledger ===
= look
VO: Sol's ticket ledger. Every pledge in the shop, in a hand so small it's practically a secret.
-> DONE
= use
SOL: Hands off the ledger, mister. That's not reading material, that's my livelihood.
-> DONE

=== pawn__caged_storage ===
= look
VO: Behind the wire, a cloth-bound book with Chinese on the cover. It looked lonely among the saxophones.
-> DONE

=== pawn__alarm_clocks ===
= look
VO: Fifty clocks, all telling a different time. On the Bowery, that's about right.
-> DONE

=== pawn__violins ===
= look
VO: Violins. You pawn the violin when the band's let you go. You pawn the case when you've stopped hoping.
-> DONE

=== pawn__sol ===
= look
VO: Sol Abramowitz. He's seen every hard-luck story on the Bowery, and he gave most of them a ticket.
-> DONE
= talk
{has_book: -> sol_after}
{has_ticket: -> sol_redeem}
-> sol_hub
= pawn_ticket
-> sol_redeem
= cigarettes
SOL: I look like a tobacconist? I look like a man with a cold. Keep your cigarettes.
-> DONE
= flask
SOL: At this hour? Put it away, I'm a respectable crook.
-> DONE

=== sol_hub ===
* [You've got a book of Lee Wing's.]
    MATT: You've got a book back there. Cloth cover, Chinese writing. It belongs to Lee Wing.
    SOL: Everything in this shop has a ticket, mister. No ticket, no story. And believe me... I've heard all the stories.
    ~ sol_refused = true
    ~ act("journal:need-ticket")
    -> sol_hub
* {sol_refused} [Who pawned it?]
    MATT: Who brought it in?
    SOL: A customer. They all look the same from this side of the counter. Hungry.
    SOL: This one, maybe hungrier. He went out the back. They like the back.
    -> sol_hub
* {sol_refused} [Lee Wing won't like this.]
    MATT: Lee Wing won't like you holding his book for ransom.
    SOL: Ransom? It's a loan, sixty cents, all legal. Tell Lee Wing I kept it dry. Tell him I didn't open it.
    VO: Sol was scared of Lee Wing. Sol is not scared of much. I filed that away.
    -> sol_hub
+ [Just looking.]
    SOL: Looking is free. Looking long is a nickel.
    -> DONE

=== sol_redeem ===
~ act("take:pawn-ticket")
SOL: Four-four-one-seven. A book, cloth, one. Sixty cents, the loan and the interest.
MATT: Sixty cents. That's lunch.
SOL: So skip lunch. You look like a man who's had practice.
~ has_book = true
~ act("give:account-book")
~ act("sfx:till")
VO: Sixty cents lighter, I had Lee Wing's book. It was heavier than it looked. Most books with names in are.
-> DONE

=== sol_after ===
SOL: You again. You want something else of somebody's? I got a trumpet, barely used. The fella barely could play.
-> DONE

// ---- THE JUNKIE -------------------------------------------------------------------------------------

=== alley__default ===
= look
{~VO: The alley behind Sol's. The Bowery's back pocket.|VO: Wet brick, wet rags, and a smell like the city's been sick in its sleep.}
-> DONE
= use
VO: Whatever's in there can stay in there.
-> DONE

=== alley__back_door ===
= use
~ act("go:pawnshop")
~ act("sfx:door")
-> DONE

=== alley__rag_heap ===
= look
VO: Rags and newspapers. Somebody's bed. Somebody's whole estate.
-> DONE

=== alley__junkie ===
= look
VO: A thin kid in a coat too big for him. Shaking, and not only from the cold.
-> DONE
= talk
{has_ticket: -> junkie_after}
-> junkie_hub
= cigarettes
-> junkie_trade
= flask
JUNKIE: Ain't drinkin' it. I want somethin' I can sell.
VO: Fair enough. I wasn't keen to part with it either.
-> DONE

=== junkie_hub ===
JUNKIE: Whatever it is, I didn't do it. And if I did, it was somebody else.
* {sol_refused} [You pawned a book at Sol's.]
    MATT: You pawned a book at Sol's. Cloth cover, Chinese on it.
    JUNKIE: Ticket? Yeah, I got a ticket. What's it to you? A pack. Make it two packs, pal, and it's yours.
    ~ act("journal:junkie-ticket")
    {has_cigs:
        VO: Two packs. I had one, and it was Kate's.
    - else:
        VO: I didn't have one pack, let alone two.
    }
    -> junkie_hub
* [You look cold.]
    MATT: You look cold.
    JUNKIE: You look like a cop. We both got problems.
    -> junkie_hub
+ [Forget it.]
    JUNKIE: Already did.
    -> DONE

=== junkie_trade ===
{not sol_refused:
    JUNKIE: Smokes? What for? What do you want?
    VO: Better find out what he's got before I hand over the only currency I own.
    -> DONE
}
MATT: One pack. Take it or don't.
JUNKIE: One? ... Aw, hell. Deal.
~ has_cigs = false
~ has_ticket = true
~ act("take:cigarettes")
~ act("give:pawn-ticket")
~ act("anim:junkie:idle")
VO: Pawn ticket four-four-one-seven, warm from his pocket.
* [Lee Wing knows a boy took it.]
    MATT: Lee Wing knows a thin boy in a big coat took it. Find another street for a while.
    JUNKIE: ...Yeah. Yeah, okay.
    VO: He didn't say thanks. I didn't expect it. Warnings are like that.
* [Say nothing.]
    VO: I let it lie. Lee Wing would find him or he wouldn't. Neither one was my rent.
- -> DONE

=== junkie_after ===
~ act("anim:junkie:cough")
~ act("sfx:cough")
JUNKIE: We're square, pal. Go away.
-> DONE


// =====================================================================================================
// P4 · LEE WING'S TEA HOUSE: THE BOOK RETURNED
// =====================================================================================================

=== lee_return ===
~ has_book = false
~ book_returned = true
~ act("take:account-book")
MATT: One account book. Thirty years of names, sixty cents of interest. I didn't read it.
LEE: No. You don't read Chinese.
MATT: I didn't try.
LEE: That is better than not reading it.
~ act("sfx:abacus")
LEE: Two weeks, Mr. Long. Then we talk again about the rent.
* [Tell him where the boy sleeps.]
    ~ told_lee_where = true
    MATT: The kid who took it sleeps behind Sol's, in the alley.
    LEE: I know where he sleeps. I wanted to know if you would tell me.
    VO: I'd passed some kind of test. I wasn't sure which side of it I'd come out on.
* [Say you didn't see his face.]
    MATT: I never got a good look at him.
    LEE: No. Nobody does, on the Bowery.
    VO: He knew. Lee always knows. He let me keep the lie, which on Doyers Street is a kind of favour.
- LEE: Slow business makes a man available, Mr. Long. I will remember that you are available.
// Lee "rent extensions for favours" (bible); seeds the Act 1 greatcoat favour.
~ act("journal:rent-two-weeks")
VO: Two weeks' grace. On Doyers Street that's practically a pension.
-> DONE

=== lee_after ===
LEE: Two weeks, Mr. Long. I have written it down. You know how I am with books.
-> DONE


// =====================================================================================================
// P5 · MATT'S OFFICE, NIGHT: INÉZ WALKS IN OUT OF THE RAIN
// Teaches: the notebook (journal) unlocks; evidence board tutorial (one link). Ends on the Act 1 card.
// Starts when Matt goes back to his office after P4.
// =====================================================================================================

=== p5_evening ===
~ act("scene:office-night")
~ act("sfx:rain")
VO: The snow turned to rain by dark. I sat in the office and let it explain things to the window.
VO: Two weeks' grace and forty-odd cents. I was doing the sums again when the knock came.
~ act("sfx:knock")
~ act("anim:inez:walk_in")
VO: She came in out of the rain like she'd paid it to stop.
VO: Platinum hair, dark eyes, a fur collar. The coat had been mended at one cuff. Rich people don't mend. They replace.
~ act("anim:inez:sit")
INEZ: They tell me you find people, Mr. Long. I need you to find one man. Quietly.
-> inez_hub

=== inez_hub ===
* [Who is he?]
    INEZ: Captain Michael Harlan. Army Medical Corps. He's a surgeon on Governors Island.
    ~ act("give:michael-photo")
    VO: She slid a photograph across the desk. Square jaw, Army collar, the kind of face they put on recruiting posters.
    -> inez_hub
* [How long has he been gone?]
    INEZ: Nine days. Since the eleventh.
    MATT: Armistice Day.
    INEZ: He hates the parades. He said he'd come to dinner after. He didn't come.
    -> inez_hub
* [What does the Army say?]
    INEZ: That he's on leave. Michael has never taken a day's leave in his life. He wouldn't know what to do with it.
    -> inez_hub
* [And the police?]
    INEZ: A detective wrote "lovers' quarrel" in his notebook and offered me his handkerchief.
    MATT: Did you take it?
    INEZ: It wasn't clean.
    -> inez_hub
* [Why me?]
    INEZ: Because you used to be a policeman, Mr. Long, and you aren't any more. Those are both recommendations.
    VO: She'd done her homework. I wondered who'd marked it.
    -> inez_hub
* [Maybe he just walked out on you.]
    MATT: Men walk out, Miss Venta. Some of them even mean it.
    INEZ: Then find him and let him tell me so. I'd like to hear it in his voice.
    VO: A society girl and a missing boyfriend. A routine job. I'd done a dozen. I told myself this was the thirteenth.
    -> inez_hub
* -> inez_deal

=== inez_deal ===
INEZ: Fifty dollars, Mr. Long. In advance.
~ act("give:money")
VO: Fifty dollars. Two months' rent, to the penny. Lee Wing would be delighted, and suspicious.
INEZ: And this. The key to his apartment. West Eighty-Fourth Street.
~ act("give:key")
* [I'll find him.]
    MATT: I'll find him.
* [I'll look. Finding's extra.]
    MATT: I'll look. Finding costs extra.
- INEZ: Quietly, Mr. Long.
~ act("anim:inez:stand")
~ act("anim:inez:walk_out")
~ act("sfx:door")
VO: She left the way she came: like the rain was hers, and she was lending it to me.
~ case_taken = true
-> notebook_unlock

=== notebook_unlock ===
~ act("unlock:notebook")
~ act("journal:case-harlan")
VO: I took out the notebook. A man who forgets what people tell him ends up believing what they meant.
// Notebook (journal) tutorial: the engine opens it here; entries so far: rent, Lee's book, the Harlan case.
-> DONE

// Evidence board tutorial: pin Michael's photo and the key, link them to "Army: on leave".
=== office__evidence_board_night ===
// engine: replaces office__evidence_board in office-night once the case is taken
= look
VO: The board. Old cases on the edges. Room in the middle for a new one.
-> DONE
= michael_photo
~ act("board:pin:michael-photo")
VO: Captain Michael Harlan, pinned in the middle where I can see him.
-> DONE
= key
~ act("board:pin:key")
VO: The key to his front door. A door nobody's answered in nine days.
-> DONE
= link_leave
// fired by the engine when the player links "Army: on leave" with "nine days gone" on the board
~ act("board:deduce:not-on-leave")
~ act("journal:lead-apartment")
~ act("unlock:map:michaels-apartment")
VO: A man who never takes leave is "on leave" for nine days, and the Army's not worried. Somebody is lying, or somebody's been told to.
VO: Start where he lived. Keys open more than doors.
~ act("card:to-be-continued")
// Card: TO BE CONTINUED / ACT 1: THE MISSING CAPTAIN
-> DONE


// =====================================================================================================
// INVENTORY: right-click descriptions
// =====================================================================================================

=== item__eviction_notice ===
= look
VO: "Notice to quit." Lee Wing's English is better than mine when there's money in it.
-> DONE

=== item__flask ===
= look
VO: My flask. Half full, or half empty, depending on the hour.
-> DONE

=== item__cigarettes ===
= look
VO: Pete's cigarettes, a Bowery brand. Kate's ration, Pete's ransom, my currency.
-> DONE

=== item__pawn_ticket ===
= look
VO: Ticket four-four-one-seven. A card that says somebody else owns a piece of your life.
-> DONE

=== item__account_book ===
= look
VO: Lee Wing's account book. I don't read Chinese, and tonight's not the night to learn.
-> DONE

=== item__money ===
= look
VO: Fifty dollars. The rent, the grocer, and a week of not answering the door.
-> DONE

=== item__michael_photo ===
= look
VO: Captain Michael Harlan, Medical Corps. Steady eyes. The kind of man who doesn't go missing by accident.
-> DONE

=== item__key ===
= look
VO: His door key. West Eighty-Fourth Street. A key to a door nobody's answered in nine days.
-> DONE

=== item__default ===
= use
{~VO: That doesn't go there.|VO: No. Even I've got standards.|VO: I tried it in my head first. It didn't work there either.}
-> DONE


// =====================================================================================================
// ENGINE CONTRACT (tags)
//   Actions are calls to the external function act("<verb>:<args>") (a tag on a line of its own would be lost
//   when no text follows it, so actions never ride on tags):
//   scene:<room>             change room (with fade)            go:<room>    walk out to a room via its exit
//   give:<item> take:<item>  inventory                          hide:<sprite-or-hotspot>  remove from the scene
//   anim:<who>:<anim>        play an animation                  sfx:<name>   one-shot sound
//   journal:<entry-id>       add a notebook entry               unlock:notebook / unlock:map:<place>
//   board:pin:<item> / board:deduce:<id>  evidence board        card:<id>    full-screen title card
//   #mask:honest / #mask:guarded  the only tag: on a choice, shows the half-mask icon (`mask` does the tracking)
//   Voice files: tools assign ids per line (p<scene>_<nnn>) at build time; a changed line regenerates only its file.
// =====================================================================================================

=== function act(command) ===
// fallback so the script runs in the ink editor / tests without the engine
~ return
