# computor-poll-bot

1️⃣ The bot must fetch current epoch computor IDs (`BROADCAST_COMPUTORS` packets).  
2️⃣ The bot must allow to link a computor ID to a Discord user by analyzing a message signed by the computor (the Discord user name will be signed for that); several computors can be linked to a single Discord user; upon epoch change the bot must revalidate links between computors and users; the bot may change user roles accordingly (by adding/removing @Computor role).  
3️⃣ The bot must allow to create polls (only by actual computors), and cast votes on them (by computors); the polls must be "sealed" right after at least 451 computors have voted.
