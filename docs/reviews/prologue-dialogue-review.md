# Prologue ("Rent Day"): dialogue review

Script: `game/ink/prologue.ink` (draft of 26 Nov 2026). Read against the bible (`docs/bible/doyers-street-game-bible.md`), `docs/decisions.md` and `docs/script/prologue-critical-path.md`.
Every line is already recorded, so this review only asks for a change where something is wrong. Most "consider" items can be left alone.

## Verdict

The Prologue is in good shape. Matt's voice-over is dry, visual and mostly one image per line, as the guide asks. The bible's sample lines sit naturally in their scenes. Pete and Kate sound like a married couple with a running joke, not like two people delivering exposition. Lee Wing is written with real dignity: he speaks formal English, never pidgin, and he is always a step ahead of Matt. The "Pete knows" beat is light and exactly right. The period texture is mostly strong and accurate: Crater, Seabury, the apple sellers, WMCA at the McAlpin, the phone company's office on West Street, Armistice Day, the June 1930 act for Chinese wives.

The real problems are few and fixable:
1. **Two anachronisms in Pete's mouth**: "psychological warfare" and "hostage situation".
2. **Matt's money doesn't add up.** He has "a dollar and change", then "forty-three cents", then pays Sol sixty cents, then has "forty-odd cents". "Two weeks' rent is eight dollars" doesn't match the $25 a month that P5 implies.
3. **Inéz never gives her name**, but Matt calls her "Miss Venta". The "What does the Army say?" choice can also come up before Matt knows the man is in the Army.
4. **Small out-of-order contradictions**, such as Sol's "back door" and Lee's two weeks of grace never being mentioned on one branch.

Fixing all the **must fix** items means re-recording about 8 lines. Fixing all the **should fix** items adds about 16 more.

Severity: **must fix** 5 · **should fix** 17 · **consider** 11.

---

## Findings, in play order

### P1 · Matt's office

**1. Money track (several knots): `office__eviction_notice.use`, `item__change.look`, `matt_self.use`, `doyers__newsboy.talk`**
- Lines:
  - `VO: Fifty dollars. I had a dollar and change, a hat, and a talent for finding things other people had lost.`
  - `VO: Forty-three cents. Two weeks' rent is eight dollars. I did the arithmetic so Kate wouldn't have to.`
  - `VO: Forty-one cents. The Clarion got the other two.`
  - `VO: Forty-three cents, a flask, and a key to an office I don't pay for.`
  - `VO: Forty-one cents, a flask, and today's bad news.`
  - `VO: Forty-one cents. I was a man of property.`
- Category: sense. Severity: **must fix**.
- Why:
  - P1 says Matt has "a dollar and change", but the item lines say 43 cents. With 43 cents he can't pay Sol 60 cents, and P5's "forty-odd cents" only works if he started with about a dollar.
  - The `cents` variable never goes down at Sol's, so these lines would still say "forty-three" after the book is redeemed.
  - "Two weeks' rent is eight dollars" means about $17 a month, but P5 says "$50 = two months' rent, to the penny", which is $25 a month.
- Fix: keep the two critical-path lines (P1 "a dollar and change", P5 "forty-odd cents"). Take the figures out of the optional lines, so they stay true whatever order the player does things in. Optionally, a programmer can set `cents` to 103 and take 60 off in `sol_redeem`; the conditions below still work either way.
  - `item__change`, first branch: `VO: Loose change. Not enough to count, so I counted it twice.`
  - `item__change`, else branch: `VO: Loose change, less two cents. The Clarion got those.`
  - `matt_self.use`, first branch: `VO: Loose change, a flask, and a key to an office I don't pay for.`
  - `matt_self.use`, else branch: `VO: Loose change, a flask, and today's bad news.`
  - `doyers__newsboy.talk`: `VO: Two cents poorer. I was still a man of property.`

**2. `matt_self.look`**: `VO: Twenty past nine. The rent was due at nine. I keep to a schedule. Just not the landlord's.`
- Category: sense. Severity: **should fix**.
- Why: the notice Matt has just read says "Fifty dollars by Saturday". The rent wasn't due at nine.
- Fix: `VO: Twenty past nine. The landlord's letter was up before I was. Most things are.`

**3. `office__telephone.use`**: `MATT: Spring seven, three one hundred.`
- Category: period. Severity: **should fix**.
- Why: in 1930, police headquarters was "Spring 3100". The NYPD's own magazine, launched that year, was named *Spring 3100* after the number. The "SPring 7-" form came with the later two-letter, five-digit numbering. I'm fairly confident, but not certain, about the date of the change; the plain form is safe either way.
- Fix: `MATT: Spring thirty-one hundred.`

**4. `office__framed_certificate_1.look`**: `VO: An NYPD commendation, 1924. They give you a frame while you're useful.`
- Category: period. Severity: consider.
- Why: "NYPD" existed, but men on the force said "the department". Spoken aloud, the initials sound like modern TV.
- Fix: `VO: A department commendation, 1924. They give you a frame while you're useful.`

### Corridor

**5. `corridor__default.look`**: `VO: Brown paint over green paint over a hundred years of tenants.`
- Category: sense. Severity: **should fix**.
- Why: the other variant in the same shuffle says the building dates from 1890, which is forty years earlier.
- Fix: `VO: Brown paint over green paint over forty years of tenants.`

**6. `corridor__office_door.look`**: `VO: Number twelve. My office, my bedroom, my address for another two days.`
- Category: sense. Severity: **should fix**.
- Why: after P4, Matt has two weeks' grace, so "two days" is wrong for the rest of the chapter.
- Fix: `VO: Number twelve. My office, my bedroom, my address, for as long as Lee Wing allows.`

### P2 · Pete & Kate's flat

**7. `flat__newspaper_on_table.look`**: `VO: Today's Clarion, folded to Pete's page. Kate reads it from the front, Pete from his own byline.`
And **`doyers__newsboy.look`**: `VO: The kid sells the Clarion on this corner every morning. Pete tips him a nickel to shout his headlines louder.`
- Category: period / sense. Severity: **should fix**.
- Why: the *Evening Clarion* is an evening paper. At 9:20 a.m. the copy on Kate's table is last night's. Pete "brings it home every night" (`corridor__newspaper`). Evening papers' first editions reached the street around late morning, not first thing.
- Fix:
  - `VO: Last night's Clarion, folded to Pete's page. Kate reads it from the front, Pete from his own byline.`
  - `VO: The kid sells the Clarion on this corner, every edition. Pete tips him a nickel to shout his headlines louder.`

**8. `read_news`**: `VO: "Apple Sellers on Every Corner." The growers' association sells them a crate on credit, and they sell the apples at a nickel each. ...`
- Category: period. Severity: **should fix** (one word).
- Why: the scheme was run by the International Apple Shippers' Association, from October 1930. The rest of the line is right: about 6,000 sellers, a nickel an apple.
- Fix: `VO: "Apple Sellers on Every Corner." The shippers' association sells them a crate on credit, and they sell the apples at a nickel each. Six thousand men with a box and a tie. I counted two of them on my block who used to be bankers.`

**9. `read_news`**: `VO: "Roosevelt Re-Elected by Record Margin." ...` (also `"Legs Diamond Will Live, Doctors Say."`)
- Category: period. Severity: consider.
- Why: these are presented as today's paper, 20 November. The election was on 4 November and the Monticello shooting on 12 October, so both headlines are two to five weeks old. Diamond's recovery was news for weeks, so that one can stay.
- Fix (Roosevelt only, if any): `VO: "Roosevelt Margin a Record, Final Count Shows." Seven hundred thousand votes. Tammany is pleased. When Tammany is pleased, somebody else is paying.`

**10. `flat__default.use`**: `VO: Kate would know. Kate always knows.`
Also `flat__teacup_3.use` (`VO: I took the cup. Kate would know. Kate always knows.`) and `tea__tea_women.talk` (`VO: Whatever it was, Lee would know. Lee always knows.`)
- Category: craft. Severity: consider.
- Why: "X always knows" comes up five times in the chapter (Pete, Kate twice, Lee twice), and the default line is heard often. Keep the ones in P1 (Pete) and P4 (Lee), where they land.
- Fix:
  - `flat__default.use`: `VO: Better not. Kate counts things.`
  - `flat__teacup_3.use`: `VO: I took the cup. Kate would have it counted by tonight.`

**11. `flat__teacup_3.use`**: `KATE: It's clean, Matt. Bring it back that way.`
- Category: voice. Severity: consider.
- Why: everywhere else Kate calls him "Matthew"; it's part of her voice.
- Fix: `KATE: It's clean, Matthew. Bring it back that way.`

**12. `flat__percolator.use`**: `VO: I had Kate's cup in my pocket. All it needed was to go under the spout.`
- Category: sense. Severity: consider.
- Why: a china cup and saucer don't go in a pocket. This is the inventory showing through.
- Fix: `VO: I had Kate's cup. All it needed was to go under the spout.`

**13. `pete_hub.pete_news`**: `MATT: The second one. I'm short on time.`
- Category: sense. Severity: **should fix** (critical path).
- Why: Pete offers "the news, or the news they let me print". Choosing the censored version doesn't follow from being short on time, and the joke doesn't come through.
- Fix: `MATT: Whichever's shorter. I've got rent to find.`

**14. `pete_hub.pete_smoke`**: `PETE: One pack a week, left on the table where I can see it. It's psychological warfare, Matt.`
- Category: period. Severity: **must fix** (critical path).
- Why: "psychological warfare" dates from about 1940 (OED) and belongs to the Second World War.
- Fix: `PETE: One pack a week, left on the table where I can see it. It's cruel and unusual punishment, Matt.` Kate's "It's arithmetic, Peter." still answers it.

**15. `pete_hub.pete_clarion`**: `PETE: Clarion's cutting staff. Every week another desk goes quiet. I'm writing twice as much so they can't hear mine.`
- Category: sense. Severity: **should fix**.
- Why: the image is backwards. He wants his desk to be heard, so that it doesn't go quiet.
- Fix: `PETE: Clarion's cutting staff. Every week another desk goes quiet. I'm typing twice as loud so mine never does.`

**16. `pete_hub.pete_last_night`** (honest branch): `MATT: A place in the Village. There was a piano player.`
- Category: sense (continuity). Severity: consider (no re-record).
- Why: players will read this as The Velvet Door and Julian. If Matt was already there the night before, then the matchbook password (1.5), "why would a straight captain come here", and Corrigan's "Didn't figure this for your kind of place" (1.6) all wobble.
- Fix: no line change. Decide now that it was a different club and a different pianist, and keep Act 1 consistent with that.

**17. `kate_hub.kate_cigs_ask`**: `PETE: This is a hostage situation.`
- Category: period. Severity: **must fix** (critical path).
- Why: "hostage situation" is police and news jargon from the 1970s.
- Fix: `PETE: That's kidnapping. I want it on the record.` This keeps the ransom joke that `item__cigarettes` picks up ("Pete's ransom").

**18. `matt_self.look`** (kate_gone branch): `VO: Noon, near enough. The snow hadn't decided whether to stay.`
- Category: sense. Severity: consider.
- Why: Kate has just left saying "And I'm late". At noon, an accountant would be three hours late. If you change it, also change `tea__tea_women.talk` `MATT: Afternoon, ladies.` to `MATT: Good day, ladies.`
- Fix: `VO: Getting on for ten. The snow hadn't decided whether to stay.`

**19. `item__cigarettes.look`**: `VO: Pete's cigarettes, a Bowery brand. Kate's ration, Pete's ransom, my currency.`
- Category: sense / period. Severity: consider.
- Why: "a Bowery brand" means nothing. A real cheap brand adds texture. Wings were launched in 1929 as a ten-cent cigarette.
- Fix: `VO: Pete's cigarettes. Wings, ten cents a pack. Kate's ration, Pete's ransom, my currency.`

### P3 · Doyers Street, tea house, pawnshop, alley

**20. `doyers__default.look`**: `VO: Doyers Street. One bend, three hundred feet, and a reputation it earned the hard way.`
- Category: period (fact). Severity: **should fix**.
- Why: Doyers Street is about 200 feet long, and it is always described that way.
- Fix: `VO: Doyers Street. One bend, two hundred feet, and a reputation it earned the hard way.`

**21. `tea__tea_women.look`**: three VO lines (the crowd joke, the exclusion laws, the June 1930 act).
- Category: craft. Severity: consider.
- Why: the history is accurate. The 13 June 1930 act admitted Chinese wives of citizens married before 26 May 1924. But three lines in a row is a small speech, which goes against "one image per line, no speeches". It's optional; if you trim, cut the middle line.

**22. `lee_first`** ("What's in it for me?" branch): `LEE: A roof. It is snowing, Mr. Long.`
- Category: sense. Severity: **should fix**.
- Why: on this branch Lee never offers the two weeks. Even so, `lee_reminder` ("My counter. Two weeks.") and P4 talk as if he did.
- Fix: `LEE: A roof, two weeks longer. It is snowing, Mr. Long.`

**23. `pawn__sol.notice`**: `SOL: Mr. Long. Again. A lucky day it isn't.`
- Category: sense. Severity: **should fix**.
- Why: this is a shuffle, so "Again" can play on Matt's first visit.
- Fix: `SOL: Mr. Long. A lucky day it isn't.`

**24. `pawn__default.use`**: `SOL: You break it, you bought it. You look at it, I'm watching.`
- Category: period. Severity: consider.
- Why: the "you break it, you bought it" formula is mostly mid-century and later. I can't place it firmly in 1930, so this is a caution, not a finding.
- Fix: `SOL: You break it, you pay. You look at it, I'm watching.`

**25. `sol_hub`**: `SOL: A customer. They all look the same from this side of the counter. Hungry.` / `SOL: This one, maybe hungrier. He went out the back. They like the back.`
- Category: sense. Severity: **should fix** (critical path).
- Why: Sol makes three fusses about nobody going through his back room ("Customers use the front"). Here a customer has walked out through it. Sol means the alley, so he should say so.
- Fix (second line only): `SOL: This one, maybe hungrier. He sleeps out back, in the alley. They like the alley.`

**26. `sol_hub`**: `SOL: Ransom? It's a loan, sixty cents, all legal. Tell Lee Wing I kept it dry. Tell him I didn't open it.`
- Category: sense. Severity: **should fix** (critical path).
- Why: later Sol charges "Sixty cents, the loan and the interest". If the loan itself was sixty cents, the interest has vanished. Taking the figure out also lets Matt's "sixty cents of interest" to Lee work as a pun.
- Fix: `SOL: Ransom? It's a loan, at the legal rate. Tell Lee Wing I kept it dry. Tell him I didn't open it.`

**27. Sol's Yiddish (several knots)**
- Category: voice. Severity: consider.
- Why: across Sol's lines there are "Nu" (three times), "mensch", "gonif", "gevalt", "gey gezunt", plus inverted syntax. Each line is fine on its own, and "There's a law, an ex-cop can't be a thief?" is a keeper. Together they edge towards stage-Yiddish.
- Fix: no re-records are needed. Just don't add more in later acts.
- Note: the critical-path doc has `SOL: Everything in this shop has a ticket...` without the "Nu," that the .ink file now has. Check which version was recorded. If it was the doc's version, leave it that way.

**28. `junkie_hub`**: `JUNKIE: Whatever it is, I didn't do it. And if I did, it was somebody else.`
- Category: craft. Severity: **should fix** (no re-record).
- Why: the greeting sits at the top of the hub, so it plays again after every choice, in the middle of the conversation. The critical-path doc shows it twice in a row.
- Fix: a programmer change. Play the line once when the conversation opens (for example, move it into `alley__junkie.talk` before the divert), and leave the choices as they are.

**29. `alley__junkie.flask`**: `JUNKIE: Ain't drinkin' it. I want somethin' I can sell.`
- Category: sense / period. Severity: **should fix**.
- Why: under Prohibition, a flask of liquor is exactly something you can sell. The refusal undercuts itself.
- Fix: `JUNKIE: Booze? I'd only drink it. Smokes I can sell.`

**30. `item__account_book.look`**: `VO: Lee Wing's account book. I don't read Chinese, and tonight's not the night to learn.`
- Category: sense. Severity: **should fix**.
- Why: Matt only has the book in the afternoon, between Sol's and the tea house.
- Fix: `VO: Lee Wing's account book. I don't read Chinese, and today's not the day to learn.`

### P5 · Matt's office, night

**31. `p5_evening`**: `INEZ: They tell me you find people, Mr. Long. I need you to find one man. Quietly.`
And **`inez_hub`**: `MATT: Men walk out, Miss Venta. Some of them even mean it.`
- Category: sense / social. Severity: **must fix**.
- Why: Inéz never introduces herself, and nothing on screen gives her name, but Matt uses it. In 1930 a woman calling on a detective at night would give her name first. That is also what makes her poise read as manners rather than mystery.
- Fix: `INEZ: Inéz Venta, Mr. Long. They tell me you find people. I need you to find one man. Quietly.`

**32. `inez_hub`** (choice order): `* [What does the Army say?]` and `* [Maybe he just walked out on you.]`
- Category: sense. Severity: **must fix** (no re-record).
- Why: both can be picked before "Who is he?". Matt can't know the man is in the Army, or that he's her man, until she tells him.
- Fix: a programmer change. Label the first choice and gate these two on it, for example `* (who) [Who is he?]` and `* {who} [What does the Army say?]`, and the same for "walked out". Nothing else in the hub changes. This adds a condition, so the writer needs to approve it.

**33. `item__money.look`**: `VO: Fifty dollars. The rent, the grocer, and a week of not answering the door.`
- Category: sense. Severity: **should fix**.
- Why: P5 has just established that fifty dollars is "two months' rent, to the penny". Nothing is left for the grocer.
- Fix: `VO: Fifty dollars. The rent to the penny, and nothing for the grocer.`

---

## Strengths to keep

- **Lee Wing.** "Fifty dollars moves me also", "I know where he sleeps. I wanted to know if you would tell me", "I will remember that you are available". He is formal and dignified, never pidgin, and quietly in charge. The captioned Cantonese for the staff and the tea women is right and respectful.
- **Pete and Kate.** The cold open ("Kate is four feet away"), "Sound reasoning. Badly dressed, but sound", "That's not a cause, Matthew. That's a symptom", "I want a lot of things" / "It's his most consistent quality". Each speaker can be told apart with the names hidden.
- **The "Pete knows" beat.** "Then go back and tell him so. Life's short, and the rent's due either way." The guarded branch ("That's what makes him dangerous to lie to") is just as good. Both meet the decisions doc (open in private) without making a speech of it.
- **Inéz's scene.** The handkerchief exchange ("It wasn't clean"), "Those are both recommendations", "I'd like to hear it in his voice", "I wondered who'd marked it". She's poised and guarded, and it sets up Whitcombe without naming anything early.
- **Sol and Matt at the back door.** "Sol, I was a cop." / "So? There's a law, an ex-cop can't be a thief?"
- **Matt's VO highlights.** "The desk was paid for", "Painted backwards from in here, like most of my life", "Some cases you close. Some you just stop looking at", "On the Bowery, cigarettes are money that burns", "Most books with names in are".
- **Period detail that is right.** Do not "correct" these:
  - Crater disappeared from West 45th Street in August 1930.
  - The Seabury magistrates' inquiry, the Women's Court framings and the bail bondsmen.
  - WMCA broadcast from the Hotel McAlpin.
  - New York Telephone's business office was on West Street.
  - Armistice Day fell on 11 November, nine days before the 20th.
  - The 1930 act for Chinese wives.
  - The Clarion costs two cents.
  - Sixty cents a pledge.
  - Twenty-five dollars a month for a Chinatown room.
