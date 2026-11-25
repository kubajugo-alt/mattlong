# Prologue: "Rent Day" — critical path, as played

Generated from `game/ink/prologue.ink` by playing the shortest route through it (one choice taken at each branch;
the other branches are in the .ink file). **VO** = Matt's voice-over; *[act …]* = what the engine does; ▸ = the choice taken.


## P1 · Matt's office, morning

*(prologue_start)*
*[act card:prologue]*  
*[act scene:office-day]*  
*[act anim:matt:wake_at_desk]*  
**VO:** Thursday. The first snow of the year was coming down on Doyers Street like it hadn't been told about the Depression.  
**VO:** I'd slept at the desk again. The desk didn't mind. The desk was paid for.  
*(office__door.use)*
**VO:** Somebody's slid something under it. Somebody wants it read before I go.  
*(office__eviction_notice.use)*
*[act give:eviction-notice]*  
*[act hide:eviction-notice]*  
*[act sfx:paper]*  
**VO:** Love letter from the landlord. He always writes when the money's late.  
**VO:** Fifty dollars by Saturday, or "vacate the premises". Lee Wing writes a nice formal English when he's annoyed.  
**VO:** Fifty dollars. I had a dollar and change, a hat, and a talent for finding things other people had lost.  
**VO:** Pete would know who'd lost something this week. Pete always knows.  
*(office__door.use)*
*[act go:corridor]*  
*(corridor__street_door_below.use)*
**VO:** Not yet. Pete hears things before the police do. I'll start next door.  

## P2 · Pete & Kate's flat

*(flat_enter)*
**PETE:** Coffee's on me. Technically it's on Kate. Don't tell Kate.  
**KATE:** Kate can hear you, Peter. Kate is four feet away.  
**VO:** The coffee was Kate's, the hangover was Pete's, and I'd brought my own.  
*(flat__pete.talk)*
▸ **Anything in the paper?**  
**PETE:** Depends. You want the news, or the news they let me print?  
**MATT:** The second one. I'm short on time.  
**PETE:** Somebody turned over Lee Wing's tea house Tuesday night. Didn't touch the till. Took his account book.  
**MATT:** His account book.  
**PETE:** Thirty years of who owes Lee Wing what. In Chinatown, that's not a book. That's a map.  
*[act journal:lee-book]*  
**VO:** Lee Wing owned the tea house, the building, and my overdue rent. A man who got his book back might forget a few dollars.  
**VO:** Might.  
**PETE:** Tong business, mark my words. "Blood on Doyers Street." I can see the headline.  
**KATE:** Pete, a story isn't true because it's exciting. It's true because it adds up.  
**PETE:** That's why I married her. Somebody's got to do the arithmetic.  
▸ **Spare a smoke, Pete?**  
**PETE:** Love to. Can't. Kate's rationing me.  
**PETE:** One pack a week, left on the table where I can see it. It's psychological warfare, Matt.  
**KATE:** It's arithmetic, Peter.  
**VO:** If I was going to the Bowery broke, I needed something to trade. On the Bowery, cigarettes are money that burns.  
▸ **See you later.**  
**PETE:** Not if I see you first. That's journalism.  
*(flat__kate.talk)*
▸ **About Pete's cigarettes...**  
**KATE:** No.  
**MATT:** I haven't asked yet.  
**KATE:** You were going to. You have your asking face on.  
▸ **It's for a good cause. Mine.**  
**MATT:** It's for a good cause. Mine.  
**KATE:** That's not a cause, Matthew. That's a symptom.  
▸ **Think of it as an investment.**  
**MATT:** Think of it as an investment. I trade the smokes for Lee Wing's book, Lee forgets the rent, you keep your neighbour.  
**KATE:** ...  
**KATE:** Sound reasoning. Badly dressed, but sound.  
*[act give:cigarettes]*  
*[act hide:petes-cigarettes]*  
**KATE:** Pete, that was this week's.  
**PETE:** This is a hostage situation.  
**KATE:** And I'm late. Some of us work with facts.  
*[act anim:kate:stand]*  
*[act hide:kate-at-table]*  
*[act sfx:door]*  
**VO:** Kate left. The flat got bigger and less sensible.  
*(flat__pete.talk)*
**PETE:** So. You walked out on the Clarion wake before the second bottle. Where'd you get to?  
▸ **A place in the Village. There was a piano player.**  *(Mask choice)*  
**MATT:** A place in the Village. There was a piano player.  
**PETE:** Yeah? Any good?  
**MATT:** He was good.  
**PETE:** Then go back and tell him so. Life's short, and the rent's due either way.  
**VO:** Pete's known for years. He's never once made it a thing. It's the one room in New York where I take my hat off.  
▸ **See you later.**  
**PETE:** Not if I see you first. That's journalism.  
*(corridor__street_door_below.use)*
*[act go:doyers-street]*  

## P3 · Doyers Street, the tea house, the pawnshop and the alley

*(tea__lee_wing.talk)*
**LEE:** Mr. Long. You read my letter.  
**MATT:** Beautiful penmanship. I was moved.  
**LEE:** Fifty dollars moves me also.  
**LEE:** Mr. Long. Someone has taken my account book. Thirty years of names. I would like it back... before anybody reads it.  
**MATT:** You want me to find it.  
**LEE:** I want it on my counter. How it gets there is your business. You have a business, I think. It says so on your door.  
▸ **And the rent?**  
**MATT:** And the rent?  
**LEE:** Bring the book, and the rent can wait two weeks.  
**LEE:** A boy was seen running toward the Bowery. Thin. A coat too big for him.  
**LEE:** Ah Ming! Cha!  
*[act journal:find-book]*  
**VO:** A thin boy, a big coat, and the Bowery. That narrowed it down to half the Bowery.  
*(pawn__sol.talk)*
▸ **You've got a book of Lee Wing's.**  
**MATT:** You've got a book back there. Cloth cover, Chinese writing. It belongs to Lee Wing.  
**SOL:** Everything in this shop has a ticket, mister. No ticket, no story. And believe me... I've heard all the stories.  
*[act journal:need-ticket]*  
▸ **Who pawned it?**  
**MATT:** Who brought it in?  
**SOL:** A customer. They all look the same from this side of the counter. Hungry.  
**SOL:** This one, maybe hungrier. He went out the back. They like the back.  
▸ **Lee Wing won't like this.**  
**MATT:** Lee Wing won't like you holding his book for ransom.  
**SOL:** Ransom? It's a loan, sixty cents, all legal. Tell Lee Wing I kept it dry. Tell him I didn't open it.  
**VO:** Sol was scared of Lee Wing. Sol is not scared of much. I filed that away.  
▸ **Just looking.**  
**SOL:** Looking is free. Looking long is a nickel.  
*(alley__junkie.talk)*
**JUNKIE:** Whatever it is, I didn't do it. And if I did, it was somebody else.  
▸ **You pawned a book at Sol's.**  
**MATT:** You pawned a book at Sol's. Cloth cover, Chinese on it.  
**JUNKIE:** Ticket? Yeah, I got a ticket. What's it to you? A pack. Make it two packs, pal, and it's yours.  
*[act journal:junkie-ticket]*  
**VO:** Two packs. I had one, and it was Kate's.  
**JUNKIE:** Whatever it is, I didn't do it. And if I did, it was somebody else.  
▸ **Forget it.**  
**JUNKIE:** Already did.  
*(alley__junkie.cigarettes)*
**MATT:** One pack. Take it or don't.  
**JUNKIE:** One? ... Aw, hell. Deal.  
*[act take:cigarettes]*  
*[act give:pawn-ticket]*  
*[act anim:junkie:idle]*  
**VO:** Pawn ticket four-four-one-seven, warm from his pocket.  
▸ **Lee Wing knows a boy took it.**  
**MATT:** Lee Wing knows a thin boy in a big coat took it. Find another street for a while.  
**JUNKIE:** ...Yeah. Yeah, okay.  
**VO:** He didn't say thanks. I didn't expect it. Warnings are like that.  
*(pawn__sol.pawn_ticket)*
*[act take:pawn-ticket]*  
**SOL:** Four-four-one-seven. A book, cloth, one. Sixty cents, the loan and the interest.  
**MATT:** Sixty cents. That's lunch.  
**SOL:** So skip lunch. You look like a man who's had practice.  
*[act give:account-book]*  
*[act sfx:till]*  
**VO:** Sixty cents lighter, I had Lee Wing's book. It was heavier than it looked. Most books with names in are.  

## P4 · Lee Wing's tea house

*(tea__lee_wing.account_book)*
*[act take:account-book]*  
**MATT:** One account book. Thirty years of names, sixty cents of interest. I didn't read it.  
**LEE:** No. You don't read Chinese.  
**MATT:** I didn't try.  
**LEE:** That is better than not reading it.  
*[act sfx:abacus]*  
**LEE:** Two weeks, Mr. Long. Then we talk again about the rent.  
▸ **Say you didn't see his face.**  
**MATT:** I never got a good look at him.  
**LEE:** No. Nobody does, on the Bowery.  
**VO:** He knew. Lee always knows. He let me keep the lie, which on Doyers Street is a kind of favour.  
**LEE:** Slow business makes a man available, Mr. Long. I will remember that you are available.  
*[act journal:rent-two-weeks]*  
**VO:** Two weeks' grace. On Doyers Street that's practically a pension.  

## P5 · Matt's office, night

*(corridor__office_door.use)*
*[act scene:office-night]*  
*[act sfx:rain]*  
**VO:** The snow turned to rain by dark. I sat in the office and let it explain things to the window.  
**VO:** Two weeks' grace and forty-odd cents. I was doing the sums again when the knock came.  
*[act sfx:knock]*  
*[act anim:inez:walk_in]*  
**VO:** She came in out of the rain like she'd paid it to stop.  
**VO:** Platinum hair, dark eyes, a fur collar. The coat had been mended at one cuff. Rich people don't mend. They replace.  
*[act anim:inez:sit]*  
**INEZ:** They tell me you find people, Mr. Long. I need you to find one man. Quietly.  
▸ **Who is he?**  
**INEZ:** Captain Michael Harlan. Army Medical Corps. He's a surgeon on Governors Island.  
*[act give:michael-photo]*  
**VO:** She slid a photograph across the desk. Square jaw, Army collar, the kind of face they put on recruiting posters.  
▸ **How long has he been gone?**  
**INEZ:** Nine days. Since the eleventh.  
**MATT:** Armistice Day.  
**INEZ:** He hates the parades. He said he'd come to dinner after. He didn't come.  
▸ **What does the Army say?**  
**INEZ:** That he's on leave. Michael has never taken a day's leave in his life. He wouldn't know what to do with it.  
▸ **And the police?**  
**INEZ:** A detective wrote "lovers' quarrel" in his notebook and offered me his handkerchief.  
**MATT:** Did you take it?  
**INEZ:** It wasn't clean.  
▸ **Why me?**  
**INEZ:** Because you used to be a policeman, Mr. Long, and you aren't any more. Those are both recommendations.  
**VO:** She'd done her homework. I wondered who'd marked it.  
▸ **Maybe he just walked out on you.**  
**MATT:** Men walk out, Miss Venta. Some of them even mean it.  
**INEZ:** Then find him and let him tell me so. I'd like to hear it in his voice.  
**VO:** A society girl and a missing boyfriend. A routine job. I'd done a dozen. I told myself this was the thirteenth.  
**INEZ:** Fifty dollars, Mr. Long. In advance.  
*[act give:money]*  
**VO:** Fifty dollars. Two months' rent, to the penny. Lee Wing would be delighted, and suspicious.  
**INEZ:** And this. His door key. West Eighty-Fourth Street.  
*[act give:key]*  
▸ **I'll find him.**  
**MATT:** I'll find him.  
**INEZ:** Quietly, Mr. Long.  
*[act anim:inez:stand]*  
*[act anim:inez:walk_out]*  
*[act sfx:door]*  
**VO:** She left the way she came: like the rain was hers, and she was lending it to me.  
*[act unlock:notebook]*  
*[act journal:case-harlan]*  
**VO:** I took out the notebook. A man who forgets what people tell him ends up believing what they meant.  
*(office__evidence_board_night.link_leave)*
*[act board:deduce:not-on-leave]*  
*[act journal:lead-apartment]*  
*[act unlock:map:michaels-apartment]*  
**VO:** A man who never takes leave is "on leave" for nine days, and the Army's not worried. Somebody is lying, or somebody's been told to.  
**VO:** Start where he lived. Keys open more than doors.  
*[act card:to-be-continued]*  
