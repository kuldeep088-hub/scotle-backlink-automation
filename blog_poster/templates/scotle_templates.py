"""
scotle_templates.py
===================
Blog article templates matching Scotle High School's actual content style.

Style reference:
- 300-450 words
- Conversational, empathetic, parent/teacher-focused
- Short punchy intro (1-3 sentences, challenges a belief)
- 3-5 sections with clear headings
- SCOTLE HIGH SCHOOL mentioned naturally in one section
- Conclusion: one philosophical sentence
- ONE backlink only at the very end in a CTA
"""

SCOTLE_ARTICLES = [
    {
        "title": "Your Child Is Not Bad at Maths",
        "intro": "Most children who struggle with maths are not struggling with numbers. They are struggling with what happens the moment they get one wrong. That is a different problem entirely.",
        "sections": [
            {
                "heading": "Where the Fear Comes From",
                "body": "Maths anxiety rarely starts with a hard problem. It starts with a moment that stings a little. A wrong answer read aloud in class. A test score circled in red, handed back publicly. A throwaway comment about how quickly someone else finished.\n\nNone of these feel like big events at the time. But children file them away. And over time, they start making decisions based on them."
            },
            {
                "heading": "It Slips Away Gradually",
                "body": "One week a child stops raising their hand. Two weeks later they have started saying they are just not a maths person. By the time a parent notices, the belief has already settled in.\n\nThe subject did not do this to them. The experience around the subject did."
            },
            {
                "heading": "What Actually Shifts Things",
                "body": "It is less about drilling more problems and more about changing what getting it wrong feels like.\n\n- Mistakes treated as information rather than failure\n- Questions welcomed without the teacher moving on before the child is ready\n- Speed taken off the table as a measure of understanding\n- The same concept explained more than one way, without impatience\n\nNone of these are dramatic changes. But they have to be deliberate."
            },
            {
                "heading": "Some Schools Are Doing This Differently",
                "body": "At SCOTLE HIGH SCHOOL in Jaipur, maths lessons are structured around comfort before speed. Children are expected to attempt before they are expected to be correct. The culture is not about performing under pressure. It is about understanding the concept first, however long that takes."
            }
        ],
        "conclusion": "When maths feels like a safe place to try, children stay curious. Curiosity, given time, becomes skill.",
        "cta": "You can learn more about their primary approach at"
    },
    {
        "title": "Why Comparing Your Child to Other Kids in Maths Usually Backfires",
        "intro": "\"Look how fast your cousin finishes.\" \"Your friend already knows tables till 12.\" \"Other children in your class are ahead.\"\n\nThe intention behind these comments is never bad. But the child is not hearing the intention.",
        "sections": [
            {
                "heading": "What the Child Actually Hears",
                "body": "When comparisons become a regular part of how a child experiences maths, something shifts. They stop asking how does this work and start asking am I behind.\n\nThat is a different headspace entirely. Once a child is focused on ranking rather than learning, participation drops, questions stop, and labels start forming. I am slow. I am not a maths person. These are not dramatic conclusions. They are quiet ones, which makes them harder to undo."
            },
            {
                "heading": "Different Is Not the Same as Slower",
                "body": "Some children grasp number patterns fast. Some need to see the concept drawn out. Some understand it perfectly but lose time under pressure. Some are just processing before they respond.\n\nNone of that signals low intelligence. NEP 2020 and NCERT frameworks both make this point: early maths education should focus on building foundations, not measuring speed against peers."
            },
            {
                "heading": "What Actually Gets Kids to Try",
                "body": "Children work harder when their effort is noticed, not just their score. When a small improvement gets named. When a wrong answer is handled calmly rather than corrected and moved past quickly. When the problem connects to something from their actual life.\n\nConfidence grows where the stakes of getting it wrong feel low. Not where they feel high."
            },
            {
                "heading": "What SCOTLE HIGH SCHOOL Does Differently",
                "body": "At SCOTLE HIGH SCHOOL in Jaipur, assessment is individual rather than comparative. There are no public rankings. The focus is on whether a child's understanding has grown, not whether they finished faster than the person next to them. The classroom is built around attempts, not performances."
            },
            {
                "heading": "What Parents Can Do Today",
                "body": "It is a simple swap. Replace comparison questions with questions about learning.\n\nInstead of asking who finished first, ask what they understood today. Instead of asking why they are slower, ask which part felt confusing.\n\nProgress tracked child-to-child is usually demoralising. Progress tracked month to month, for the same child, usually is not."
            }
        ],
        "conclusion": "Academic confidence is built on clarity and steady encouragement. Comparison tends to get in the way of both.",
        "cta": "If you are exploring a primary programme that focuses on concept-building over comparison, learn more about SCOTLE HIGH SCHOOL at"
    },
    {
        "title": "A Small Classroom Moment That Explained Maths Anxiety",
        "intro": "A child solved a problem correctly. Erased it. Solved it again. Erased it again. Only handed it in when the teacher walked over and stood beside the desk.\n\nThe answer was right both times. The confidence was not.",
        "sections": [
            {
                "heading": "Anxiety Does Not Always Look Dramatic",
                "body": "It looks like hesitation. Silence when a question gets asked. Eyes down when the teacher scans the room.\n\nA lot of children who seem checked out in maths are not bored. They are afraid of being wrong in front of other people. That fear does not quieten down during the lesson. It gets louder."
            },
            {
                "heading": "The Primary Years Are Where It Sets In",
                "body": "Primary school is where this fear either settles in or gets cleared out.\n\nA child who reaches Class 5 already believing they are bad at maths does not just have a knowledge gap. They have a belief gap. The belief filters every future maths lesson before it even begins. That is much harder to fix than a missed concept."
            },
            {
                "heading": "What Teachers Can Do",
                "body": "- Explain the same idea more than one way, without frustration\n- Treat wrong answers as starting points rather than problems to move past\n- Build step by step before adding any pressure\n- Drop speed as a signal of how well someone understands\n\nSmall shifts in the room. Large shifts in how safe it feels to try."
            },
            {
                "heading": "How SCOTLE HIGH SCHOOL Approaches This",
                "body": "At SCOTLE HIGH SCHOOL in Jaipur, the maths programme is built around emotional safety before performance. Classes are interactive, and children can attempt problems without the answer becoming a classroom event. The structure is step-by-step, each concept confirmed before the next one is introduced."
            }
        ],
        "conclusion": "When maths feels safe today, it becomes manageable tomorrow. By secondary school, manageable tends to become confident.",
        "cta": "You can learn more about their primary approach at"
    },
    {
        "title": "The Real Reason Children Stop Trying in Maths",
        "intro": "Most of the time when a child stops trying in maths, it is not laziness. It is a risk calculation. Somewhere along the way they decided that trying, and being wrong in front of people, costs more than it is worth. So they stopped.",
        "sections": [
            {
                "heading": "When Trying Feels Risky",
                "body": "Kids are natural risk-takers in most things. They will climb things, attempt things, try things they have never done before.\n\nBut in maths classrooms, they learn quickly that some risks come with public consequences. Being wrong, in front of classmates, while a teacher moves on to the next problem, is a specific kind of exposure. The lesson it teaches is not about numbers. It is social. Keep quiet unless you are certain.\n\nAnd so they stop raising their hand. Then they stop working through the problem at all."
            },
            {
                "heading": "The Effort Disappears Before the Marks Do",
                "body": "Parents and teachers usually notice the grades first. But the effort disappeared weeks earlier.\n\nThe child started copying instead of thinking. Leaving blanks. Sitting and waiting for the period to end. By the time the test comes back with a poor score, it has already been going on for a while."
            },
            {
                "heading": "More Practice Does Not Fix This",
                "body": "Additional worksheets do not help. Extra tuition does not help on its own.\n\nWhat changes things is changing the environment. A class where wrong answers are genuinely fine. A teacher who pauses and re-explains without making it an event. A programme that cares about understanding more than it cares about pace.\n\nWhen the environment shifts, children start trying again. Not because someone pushed them. Because it finally feels worth it."
            },
            {
                "heading": "SCOTLE HIGH SCHOOL's Approach",
                "body": "SCOTLE HIGH SCHOOL in Jaipur builds its primary programme on this. Structured teaching. Activity-based learning. A classroom culture where questions are expected and attempts are welcomed, correct or not. Getting it wrong is not an event there. It is just part of learning."
            }
        ],
        "conclusion": "Children do not give up on maths. They give up on environments where trying feels too costly.",
        "cta": "To learn more about their approach to primary education, visit"
    },
    {
        "title": "Why Speed Tests Are Not Measuring What You Think They Are",
        "intro": "A timed maths test is good at measuring exactly one thing: how quickly a child can produce answers while a clock is running.\n\nThat is not the same as understanding maths. It is not even close.",
        "sections": [
            {
                "heading": "What Happens Inside During a Timed Test",
                "body": "When children know they are being timed, the part of the brain managing anxiety starts competing with the part doing the calculation. For many kids, especially those who process carefully rather than quickly, this means they go blank on problems they could solve easily without the pressure.\n\nThe test records that as a gap. The gap is not real. But the record is."
            },
            {
                "heading": "The Label That Follows",
                "body": "Low scores on timed tests become identities faster than you would expect.\n\n\"I am bad at maths\" often starts here. Not because the child cannot do the maths. They usually can, just not at that pace, under that pressure. But once the label forms, it filters every future maths experience. They stop attempting things they might actually be able to do."
            },
            {
                "heading": "What Good Assessment Actually Checks",
                "body": "The things worth measuring in a maths assessment:\n\n- Does the child understand the concept?\n- Can they apply it somewhere different from where they first saw it?\n- Can they talk through their thinking, not just produce an answer?\n- Has their understanding grown compared to last month?\n\nSpeed matters eventually, as a side effect of deep understanding. It should not be the thing being tested."
            },
            {
                "heading": "How SCOTLE HIGH SCHOOL Tests Differently",
                "body": "SCOTLE HIGH SCHOOL in Jaipur assesses children on understanding and progression, not on how quickly they complete a task. The goal is to get an accurate picture of where each child actually is, not how they perform under artificial pressure."
            }
        ],
        "conclusion": "A child who understands maths slowly still understands maths. That is the thing that matters.",
        "cta": "You can learn more about their assessment and teaching approach at"
    },
    {
        "title": "Maths Is Not a Talent. It Is a Skill.",
        "intro": "Some children hear from a very early age that they are just not maths people. Parents say it casually. Sometimes teachers imply it. Kids absorb it as fact.\n\nIt is not true. But that is almost beside the point, because once they believe it, it starts acting like it is.",
        "sections": [
            {
                "heading": "The Myth of the Maths Brain",
                "body": "Mathematical ability is not something you either have or you do not. Neuroscience is fairly clear on this: numerical reasoning develops through exposure and practice, in environments where it is safe to be wrong and try again.\n\nWhen children are told they are not maths people, they stop practising. When they stop practising, the belief becomes self-confirming. It looks like a lack of ability. It was always a lack of practice in the right conditions."
            },
            {
                "heading": "What Actually Determines Maths Confidence",
                "body": "The research tends to point toward environment more than anything else.\n\nChildren who build strong maths foundations usually have one thing in common: at some point, at school or at home, getting it wrong was okay. Trying again was normal. The process mattered more than whether the answer was right the first time."
            },
            {
                "heading": "Why the Early Years Matter So Much",
                "body": "By Class 4 or 5, most children have already decided whether maths is something they can do.\n\nPrimary school is the window. Not to accelerate or compete, but to build the belief that maths is figure-out-able. That a child who keeps going will get there. That not understanding yet is different from not being able to understand."
            },
            {
                "heading": "SCOTLE HIGH SCHOOL's Philosophy",
                "body": "At SCOTLE HIGH SCHOOL in Jaipur, no child gets labelled early. Every concept is taught with patience and structure. The focus is on building the belief alongside the skill, because one without the other usually collapses somewhere in secondary school."
            }
        ],
        "conclusion": "Talent is rare. The right environment is something adults can actually create.",
        "cta": "Learn more about how they approach primary maths education at"
    },
    {
        "title": "What Primary School Maths Should Actually Be Teaching",
        "intro": "By Class 5, children should have more than the right answers.\n\nThey should have a working relationship with numbers. A sense that maths is something you can figure out, not something that just happens to you or does not.",
        "sections": [
            {
                "heading": "The Foundation That Gets Skipped",
                "body": "Most primary maths programmes cover the content. Addition, subtraction, multiplication, fractions. The curriculum moves through it all.\n\nWhat often gets skipped is the layer underneath: making an attempt feels safe. Not knowing the answer yet is temporary. Maths is a process, not a performance.\n\nWithout that foundation, the content does not stick the way it should."
            },
            {
                "heading": "What Maths Confidence Actually Looks Like",
                "body": "The confident maths student is not necessarily the fastest in the room.\n\nThey are the child who reads a problem twice, tries something, realises it is not working, adjusts, and tries again. The willingness to do all of that, attempt, adjust, persist, is the real output of good primary maths teaching. It is more durable than any specific piece of content."
            },
            {
                "heading": "Why It Matters More Than the Grade",
                "body": "A child who finishes primary school with average marks but genuine confidence in their ability to figure things out will usually outperform a child with high marks and deep anxiety by Class 9.\n\nSecondary maths is harder. It requires persistence. Persistence requires confidence. Confidence has to be built somewhere, and primary school is where that either happens or it does not."
            },
            {
                "heading": "How SCOTLE HIGH SCHOOL Builds This",
                "body": "At SCOTLE HIGH SCHOOL in Jaipur, the primary programme is built around concept clarity, activity-based learning, and a classroom that makes attempting feel normal. The goal is not children who recite answers. It is children who are willing to try, and who know what to do when the first approach does not work."
            }
        ],
        "conclusion": "The most valuable thing primary school can give a child in maths is not a grade. It is a reason to keep going when things get hard.",
        "cta": "You can find out more about their approach to primary education at"
    },
    {
        "title": "Why Some Children Shut Down in Maths",
        "intro": "Some children go quiet in maths class. Stop raising their hand, stop asking questions. They sit through the lesson waiting for it to end.\n\nThat is not a maths problem. It is a confidence problem, and it has a pretty specific cause.",
        "sections": [
            {
                "heading": "Shutting Down Is Protection, Not Giving Up",
                "body": "At some point, the child was wrong in a way that felt embarrassing. In front of classmates. In front of a teacher who moved on quickly. And they ran the numbers.\n\nThe risk of trying was higher than the reward of getting it right.\n\nSo they stopped. Not because they could not do it. Because it stopped feeling safe to try."
            },
            {
                "heading": "What Brings Them Back",
                "body": "It is not more practice. Not pressure. Not a serious talk about how important maths is for their future.\n\nWhat brings a child back is a different experience in the room. A teacher who responds to a wrong answer with curiosity rather than correction. A moment where someone else tries something, gets it wrong, and nothing bad happens. A small success that gets noticed and named.\n\nThe threshold for re-engagement is lower than parents often think. But the environment has to change first."
            },
            {
                "heading": "The Window Is Longer Than You Think",
                "body": "Children can rebuild maths confidence at any point in primary school. Class 3. Class 5. Even into Class 6.\n\nBut they cannot do it in the same environment that shut them down. Effort without a changed environment just produces the same result and confirms the belief that they genuinely cannot do it."
            },
            {
                "heading": "SCOTLE HIGH SCHOOL's Approach to Rebuilding Confidence",
                "body": "SCOTLE HIGH SCHOOL in Jaipur builds its classrooms with this kind of child in mind. Structured progression. Patient re-teaching when something has not landed. A culture where attempting is always the right answer, regardless of whether the attempt was correct."
            }
        ],
        "conclusion": "A child who has shut down in maths has not given up on maths. They have given up on a specific environment. Change the environment.",
        "cta": "Learn more about how SCOTLE HIGH SCHOOL supports primary learners at"
    },
    {
        "title": "The One Question Every Parent Should Ask About Their Child's Maths Class",
        "intro": "Not \"What score did you get?\"\n\nNot \"Are you ahead of the class?\"\n\nThe question worth asking is: does your child feel safe being wrong in maths?",
        "sections": [
            {
                "heading": "Why This Matters More Than the Score",
                "body": "A child who feels safe being wrong will try things. They will ask questions. They will attempt a different method when the first one does not work. They will keep going.\n\nA child who does not feel safe being wrong avoids all of that. And avoidance, sustained over a few months, looks almost identical to inability. Parents often cannot tell the difference, which is part of what makes this hard to catch early."
            },
            {
                "heading": "How to Tell",
                "body": "Ask your child what happens in class when someone gets an answer wrong.\n\nIf they say the teacher explains it again, or they work through it together, the classroom is doing something right.\n\nIf they say people laugh, or the teacher moves on, or \"I don't know, I never answer\" — something needs to change."
            },
            {
                "heading": "What a Safe Maths Classroom Actually Looks Like",
                "body": "- Wrong answers are treated as useful information, not embarrassing failures\n- Children are asked to talk through their thinking, not just produce a number\n- Speed is not used as a measure of how smart someone is\n- Every child is expected to attempt, not expected to be correct from the start"
            },
            {
                "heading": "How SCOTLE HIGH SCHOOL Creates This",
                "body": "SCOTLE HIGH SCHOOL in Jaipur has built its primary maths programme around emotional safety as the foundation. Children are assessed on understanding and genuine effort, not on pace or how they compare to each other. The classroom culture is one where trying is always the right move."
            }
        ],
        "conclusion": "Safe classrooms produce confident learners. And confident learners tend to produce results that marks alone cannot predict.",
        "cta": "To learn more about how they structure primary maths education, visit"
    },
    {
        "title": "Why Homework Is Not Fixing Your Child's Maths Problem",
        "intro": "More worksheets. More practice problems. More repetition.\n\nIf this was working, it would have worked by now.",
        "sections": [
            {
                "heading": "Repeating the Wrong Thing Does Not Help",
                "body": "When a child has not understood a concept, doing it ten more times does not close the gap. It just makes the confusion faster.\n\nHomework built on a concept the child never properly grasped does not build skill. What it builds is frustration, avoidance, and eventually the belief that no amount of effort will make maths make sense."
            },
            {
                "heading": "What the Homework Struggle Is Actually Showing You",
                "body": "Homework resistance is not really a homework problem. It is a signal.\n\nSomewhere back in the concept chain, a step was skipped. A foundation was assumed that was not actually there. A lesson moved forward before understanding was confirmed. The homework is just where it becomes visible, usually at 9pm, which is the worst possible time for everyone."
            },
            {
                "heading": "What Actually Has to Happen",
                "body": "The concept needs to be re-taught. Not just repeated, re-taught. A different example. A different approach. Time for questions. No pressure to get through it quickly.\n\nThat is very hard to do at the kitchen table at night. It needs the right classroom environment, built specifically for it."
            },
            {
                "heading": "How SCOTLE HIGH SCHOOL Handles This",
                "body": "At SCOTLE HIGH SCHOOL in Jaipur, lessons are built around concept clarity before progression. No topic moves forward until the foundation is confirmed. Re-teaching is part of the planned structure, not treated as a setback, but as normal practice."
            }
        ],
        "conclusion": "Practising the wrong process more produces better confusion, not better maths. What children need is the right foundation, taught with patience.",
        "cta": "Learn more about their structured primary programme at"
    },
]


def get_scotle_article(index: int = None) -> dict:
    """Return a Scotle-style article. Random if index not specified."""
    import random
    if index is not None:
        return SCOTLE_ARTICLES[index % len(SCOTLE_ARTICLES)]
    return random.choice(SCOTLE_ARTICLES)


def get_all_scotle_articles() -> list:
    """Return all Scotle-style articles."""
    return SCOTLE_ARTICLES


def article_to_markdown(article: dict, target_url: str) -> str:
    """
    Convert a Scotle article dict to Markdown with ONE backlink at the end.
    Matches the exact style of the reference posts.
    """
    lines = []

    # Title
    lines.append(f"# {article['title']}\n")

    # Intro
    lines.append(article["intro"])
    lines.append("")

    # Sections
    for section in article["sections"]:
        lines.append(f"## {section['heading']}\n")
        lines.append(section["body"])
        lines.append("")

    # Conclusion
    lines.append("---\n")
    lines.append(article["conclusion"])
    lines.append("")

    # ONE backlink — at the very end in CTA
    lines.append(f"{article['cta']}: [{target_url}]({target_url})")

    return "\n".join(lines)


def article_to_html(article: dict, target_url: str) -> str:
    """
    Convert a Scotle article dict to HTML with ONE backlink at the end.
    """
    import re

    def md_to_simple_html(text):
        # Convert bullet points
        lines = text.split("\n")
        result = []
        in_list = False
        for line in lines:
            if line.startswith("- "):
                if not in_list:
                    result.append("<ul>")
                    in_list = True
                result.append(f"<li>{line[2:]}</li>")
            else:
                if in_list:
                    result.append("</ul>")
                    in_list = False
                if line.strip():
                    result.append(f"<p>{line}</p>")
        if in_list:
            result.append("</ul>")
        return "\n".join(result)

    parts = []
    parts.append(f"<h1>{article['title']}</h1>")
    parts.append(md_to_simple_html(article["intro"]))

    for section in article["sections"]:
        parts.append(f"<h2>{section['heading']}</h2>")
        parts.append(md_to_simple_html(section["body"]))

    parts.append("<hr>")
    parts.append(f"<p><em>{article['conclusion']}</em></p>")
    parts.append(
        f'<p>{article["cta"]}: <a href="{target_url}">{target_url}</a></p>'
    )

    return "\n".join(parts)
