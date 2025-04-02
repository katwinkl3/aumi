# Mapping out website links with Aumu


To do
<s>- Add traffic navigation - get users current location</s>
- Adopt proper compoenents from chakra
- Set up dark and light mode so colors display properly
- Test zoom
- Register user info + save chat data
- Add video and image parsing
- Add proper non-local cache for scrapper calls
- Add rate limiter
- Add tests


Challenges:
1. Reducing token size - parsed html can be more refined, could experiment with prompts or even making your own model for address parsing
2. Address relevance - how do we guarantee the address returned are correct and relevant, for different mediums
3. Cost efficiency - things to consider: cache url -> placeInfo, swap to MapBox or try to integrate it w GMaps in the future
4. Performance + security (not a problem for now) - telegram chat and input validation, *rate limiting*, queuing requests (but scrapper processing time is already quite long)

Future features:
- Past URL views can be managed (merge multiple lists)
- Expand to beyond cafes
- Allow for edits (possibly shared across group chat with delta sync though its not very useful at this point)
