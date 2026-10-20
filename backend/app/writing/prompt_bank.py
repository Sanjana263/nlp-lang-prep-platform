"""IELTS Writing Task 2 question bank: seed data for the writing_prompts table.

Run `python -m scripts.seed_writing_prompts` (from backend/) to load these into the database.
The app itself never reads this file; it reads the table. To add more questions later, either
append to PROMPT_BANK and re-run the seed script (it skips questions that already exist), or
insert rows directly in the database.

Each entry is (topic, question_type, prompt_text).
question_type is one of: opinion, discuss_both, problem_solution, advantages_disadvantages, two_part.
"""

PROMPT_BANK: list[tuple[str, str, str]] = [
    # ---------------------------------------------------------------- Education
    ("Education", "discuss_both", "Some people believe that university education should be free for all students. Discuss both views and give your opinion."),
    ("Education", "opinion", "Some people think children should start learning a foreign language at primary school. To what extent do you agree or disagree?"),
    ("Education", "opinion", "Some people believe that students should be allowed to choose all the subjects they study at school. To what extent do you agree or disagree?"),
    ("Education", "advantages_disadvantages", "More and more students are choosing to study abroad. Do the advantages of this trend outweigh the disadvantages?"),
    ("Education", "discuss_both", "Some people think schools should focus on academic subjects, while others believe that practical skills such as cooking and managing money are more important. Discuss both views and give your opinion."),
    ("Education", "opinion", "Some people say that exams are not a fair way to measure a student's ability. To what extent do you agree or disagree?"),
    ("Education", "problem_solution", "In many countries, a growing number of young people leave school without basic reading and writing skills. What are the causes of this problem, and what can be done to solve it?"),
    ("Education", "two_part", "Many people believe that online courses will eventually replace classroom teaching. Why might this happen, and is it a positive development?"),

    # --------------------------------------------------------------- Technology
    ("Technology", "advantages_disadvantages", "Some people say that technology has made our lives more complicated. Do the advantages of technology outweigh the disadvantages?"),
    ("Technology", "opinion", "Some people think that robots and artificial intelligence will take over most jobs in the future. To what extent do you agree or disagree?"),
    ("Technology", "problem_solution", "Many young people spend several hours a day on social media. What problems can this cause, and how can they be solved?"),
    ("Technology", "discuss_both", "Some people believe that children should have their own smartphones from a young age, while others think this is harmful. Discuss both views and give your opinion."),
    ("Technology", "opinion", "Some people argue that the internet has made people less willing to meet each other face to face. To what extent do you agree or disagree?"),
    ("Technology", "two_part", "Nowadays many people get their news from social media instead of newspapers or television. Why is this happening, and is it a positive or negative development?"),
    ("Technology", "opinion", "Governments should place stricter controls on how companies collect and use people's personal data online. To what extent do you agree or disagree?"),

    # -------------------------------------------------------------- Environment
    ("Environment", "problem_solution", "Many cities now have more cars than ever. What problems does this cause, and what measures could be taken to solve them?"),
    ("Environment", "opinion", "Some people believe that individuals can do little to protect the environment and that only governments and large companies can make a difference. To what extent do you agree or disagree?"),
    ("Environment", "problem_solution", "The amount of plastic waste in oceans and rivers is increasing. What are the causes of this, and what can be done about it?"),
    ("Environment", "discuss_both", "Some people think that protecting wildlife and natural areas is more important than economic development. Others disagree. Discuss both views and give your opinion."),
    ("Environment", "opinion", "Some people say that governments should tax products and activities that harm the environment, such as air travel and petrol. To what extent do you agree or disagree?"),
    ("Environment", "two_part", "In many cities, parks and green spaces are disappearing as new buildings take their place. Why is this happening, and what can be done to protect them?"),
    ("Environment", "advantages_disadvantages", "Many countries are encouraging the use of renewable energy such as solar and wind power. What are the advantages and disadvantages of this development?"),

    # ------------------------------------------------------------------- Health
    ("Health", "problem_solution", "In many countries, more and more children are becoming overweight. What are the causes of this, and what solutions can you suggest?"),
    ("Health", "opinion", "Some people believe that governments should spend more money on preventing illness through public health campaigns than on treating patients in hospitals. To what extent do you agree or disagree?"),
    ("Health", "discuss_both", "Some people think that sport should be a compulsory subject at school, while others believe students should be free to choose. Discuss both views and give your opinion."),
    ("Health", "two_part", "People in most countries are living longer than in the past. What problems might this cause for society, and what can be done about them?"),
    ("Health", "opinion", "Some people say that advertising of unhealthy food should be banned. To what extent do you agree or disagree?"),
    ("Health", "advantages_disadvantages", "Many people now use fitness apps and wearable devices to monitor their health. Do the advantages of this outweigh the disadvantages?"),

    # --------------------------------------------------------------------- Work
    ("Work", "opinion", "Some people believe that employees work better when they have flexible hours and can work from home. To what extent do you agree or disagree?"),
    ("Work", "discuss_both", "Some people prefer to stay in the same job for most of their working life, while others prefer to change jobs regularly. Discuss both views and give your opinion."),
    ("Work", "advantages_disadvantages", "More and more people are choosing to work as freelancers instead of working for a company. Do the advantages of this trend outweigh the disadvantages?"),
    ("Work", "discuss_both", "Some people say that a high salary is the most important factor in choosing a job, while others think that job satisfaction matters more. Discuss both views and give your opinion."),
    ("Work", "problem_solution", "Stress at work is becoming a serious problem in many countries. What are the causes of this, and what can employers and governments do to reduce it?"),
    ("Work", "opinion", "Some people think that the retirement age should be raised because people are living longer. To what extent do you agree or disagree?"),
    ("Work", "two_part", "A growing number of young people are starting their own businesses instead of working for others. Why is this happening, and is it a positive development?"),

    # ------------------------------------------------------------------ Society
    ("Society", "discuss_both", "Some people think that parents should be strict with their children, while others believe that a more relaxed approach is better. Discuss both views and give your opinion."),
    ("Society", "problem_solution", "In many big cities, more and more people live alone and feel lonely. What problems does this cause, and how can they be addressed?"),
    ("Society", "opinion", "Some people say that it is better for children to grow up in the countryside than in a big city. To what extent do you agree or disagree?"),
    ("Society", "two_part", "Young people today spend less time with their grandparents and older relatives than in the past. Why is this happening, and what effect does it have on families?"),
    ("Society", "opinion", "Some people believe that volunteering should be a compulsory part of education for young people. To what extent do you agree or disagree?"),

    # -------------------------------------------------------------------- Crime
    ("Crime", "discuss_both", "Some people believe that the best way to reduce crime is to give longer prison sentences. Others think there are better alternatives. Discuss both views and give your opinion."),
    ("Crime", "opinion", "Some people think that young offenders should be punished in the same way as adults. To what extent do you agree or disagree?"),
    ("Crime", "problem_solution", "In many cities, crimes such as theft and vandalism are becoming more common. What are the causes of this, and what can be done to reduce them?"),

    # ---------------------------------------------------------- Culture and travel
    ("Culture and travel", "discuss_both", "Some people think that governments should fund the arts, while others believe that money should be spent on public services instead. Discuss both views and give your opinion."),
    ("Culture and travel", "opinion", "Some people say that traditional customs and festivals are becoming less important as the world becomes more connected. To what extent do you agree or disagree?"),
    ("Culture and travel", "two_part", "Global brands and international food chains can now be found in almost every country. Why is this, and does it have a positive or negative effect on local cultures?"),
    ("Culture and travel", "advantages_disadvantages", "Tourism has become the main source of income for many places. What are the advantages and disadvantages of this?"),
    ("Culture and travel", "opinion", "Some people believe that museums and historical sites should be free to enter for everyone. To what extent do you agree or disagree?"),
    ("Culture and travel", "opinion", "Some people say that international travel makes people more tolerant of other cultures. To what extent do you agree or disagree?"),

    # ------------------------------------------------------ Cities and economy
    ("Cities and economy", "opinion", "Public transport should be free for everyone in order to reduce traffic and pollution. To what extent do you agree or disagree?"),
    ("Cities and economy", "problem_solution", "Housing costs in big cities are rising sharply, and many people can no longer afford to live there. What are the causes of this, and what can be done?"),
    ("Cities and economy", "opinion", "Some people believe that governments should spend money on public services such as healthcare and education rather than on space exploration. To what extent do you agree or disagree?"),
    ("Cities and economy", "discuss_both", "Some people think that the best way to reduce traffic is to build more roads, while others believe that investing in public transport is a better solution. Discuss both views and give your opinion."),
    ("Cities and economy", "advantages_disadvantages", "Many people now do their shopping online instead of visiting shops. Do the advantages of this trend outweigh the disadvantages?"),
    ("Cities and economy", "problem_solution", "The gap between rich and poor is growing in many countries. What problems might this cause, and what can governments do about it?"),
    ("Cities and economy", "opinion", "Some people believe that rich countries should give more financial help to poorer countries. To what extent do you agree or disagree?"),
    ("Cities and economy", "advantages_disadvantages", "More and more companies are moving their factories to other countries where labour is cheaper. What are the advantages and disadvantages of this for the company's home country?"),

    # ----------------------------------------------------------------- Language
    ("Language", "opinion", "Some people believe that English should be the only language used in international business and science. To what extent do you agree or disagree?"),
    ("Language", "problem_solution", "Many minority languages around the world are in danger of disappearing. What problems does this cause, and what can be done to protect them?"),
    ("Language", "two_part", "More and more people around the world are learning English as a second language. Why is this happening, and what are the effects on other languages?"),
]
