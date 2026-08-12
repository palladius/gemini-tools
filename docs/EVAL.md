# LLM Evaluation Plan

## Define Success: What constitutes a successful outcome for your agent?

When I say "create an image of Riccardo" or of my sons Ale and Seby I want:

1. P1 The image/video to actually be loyal to my initial prompt and idea.
2. P2 The image/video should also be realistic (no water going upside down ..)
3. P0 I want **character consistency**, which means that every character in the image/video should actually 
   look similar to the original

Note that LLMs nowadayas are BAD at character consistency (particularly for minors) but good at evaluating. This means that with enough money, a proper loop can guarantee good results - eventually.

##  Identify Critical Tasks: What are the essential tasks your agent must accomplish?

1. Generate images with well-known characters inside.
2. Generate videos with well-known characters inside.
3. Chracters need to be CONSISTENT in two parts:
  1. With the initial images of riferimento
  2. Among them (say you have a multi-chapter video of Riccardo with an elf, if the elf face changes from Legolas to Elrond its game over)

## Choose Relevant Metrics: What metrics will you track to measure performance?

We can start with a 0.0 .. 10.0 rensemblance score. An 8 is usually sufficiently good, 9 is super, 7 is meh (anyone can identify its not the person if you know them well but might be confused if they dont), anything from 6- is something to throw away.

If multiple characters are in a photo, scene, video., we would have an array of resemblance (riccardo: 8.0, alessandro: 5.6). It's also usefule to have a feedback loop in form of STRING to piggyback to the model (no beard, wrong glasses).

Maybe also cross-rate input images can help; for instance, we could find that for Riccardo sample image 1..10 the image #7 is getting poor scores vs the other 9, which could be a good feedback to actually remove/change sample.

## Cavetas and tips

1. Consistency in Cartoons is TOO EASY, so it's a non-goal. We want photo-realistic pics.
2. With Gemini models, Generation of video of kids is problematic, but its not for images (!). This means we can actually overcome the model limitaiton by decomposing the problem in: 
  1. First, create an image of minor.
  2. Animate image into a video providing the generated image as first frame of the video. Veo allows for this.
