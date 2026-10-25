/* learn.js: the #/learn route (Learn to see underwater).
 * Registers with the site router (window.AGU) and also runs on its own for previews.
 * Content first (edit freely), engine below. */
(function () {
  "use strict";

  /* ============================== CONTENT ============================== */
  var PATHS = [
    { id: "all", label: "Show everything", sub: "all nine modules", mods: [1, 2, 3, 4, 5, 6, 7, 8, 9], text: "All nine modules, about 20 hours, then the capstones." },
    { id: "policy", label: "Policy, no coding", sub: "read and try the demos", mods: [2, 4, 5, 9], read: true, text: "Modules 02, 04, 05 and 09, read on the page with their demos, about 4 hours. The notebooks are optional. Then the policy memo in Capstone C." },
    { id: "new", label: "New to coding with images", sub: "start at the surface", mods: [1, 2, 3, 4, 5, 6, 7, 8, 9], text: "All nine modules in order, about 20 hours. Then the orientation capstone and the capstone for your workstream." },
    { id: "ml", label: "I know Python and ML", sub: "but not images", mods: [2, 3, 5, 7, 8, 9], text: "Modules 02, 03, 05, 07, 08 and 09, about 13.5 hours. Skim 01 and 04 for the project’s conventions; 06 is optional." },
    { id: "m1", label: "Monitoring workstream", sub: "wildlife near the facility", mods: [1, 2, 4, 5, 6, 9], text: "Modules 01, 02, 04, 05, 06 and 09, about 12.5 hours. Then the orientation capstone and Capstone A." },
    { id: "m2", label: "Aquaculture workstream", sub: "size, growth and welfare", mods: [1, 2, 3, 5, 7, 8, 9], text: "Modules 01, 02, 03, 05, 07, 08 and 09, about 15 hours. Then the orientation capstone and Capstone B." },
    { id: "track", label: "Tracking and behaviour", sub: "counting and movement", mods: [1, 3, 7, 8, 9], text: "Modules 01, 03, 07, 08 and 09, about 11 hours. Then the behaviour tasks in Capstone B, or your own footage." }
  ];

  var TOUR = [
    { title: "A picture is numbers", preset: { dist: 1.5, water: "clear_ocean", light: 1, view: "camera", thr: 0.08 },
      body: "<p>A camera doesn’t record fish. It records a grid of tiny squares, called pixels, and three numbers for each one: how much red, green and blue light arrived there.</p><p class=\"lc-try\">Tap or click anywhere on the picture to read the numbers behind that pixel. Try a fish, then the water.</p>" },
    { title: "Water steals colour", preset: { dist: 6, water: "coastal", light: 1, view: "camera", thr: 0.08 },
      body: "<p>Light fades as it travels through water, and red fades first. Particles in the water also scatter daylight into the lens, adding a haze the colour of the sea.</p><p class=\"lc-try\">Drag the distance slider. Watch the red bar collapse and the orange fish turn the colour of the water.</p>" },
    { title: "How a computer finds a fish", preset: { dist: 3, water: "coastal", light: 1, view: "diff", thr: 0.08 },
      body: "<p>A simple detector asks one question of every pixel: how different is it from the background? Pixels that differ enough are grouped into blobs, and each blob gets a box.</p><p class=\"lc-try\">Switch the view between Picture, Difference, Mask and Boxes to watch each step. Then move the sensitivity slider.</p>" },
    { title: "Missing isn’t gone", preset: { dist: 3.5, water: "turbid_harbour", light: 1, view: "boxes", thr: 0.08 },
      body: "<p>Now the same five fish sit in murky harbour water. The detector misses fish it found easily in clearer water, yet every fish is still there.</p><p>If murky water is common near an outfall, a camera survey there will count fewer fish, even if the outfall harms none. Mistaking “the camera stopped seeing” for “the animals left” is the most important error this course teaches you to avoid.</p>" },
    { title: "Ask good questions", preset: { dist: 5, water: "coastal", light: 0.25, view: "boxes", thr: 0.08 },
      body: "<p>Dusk adds noise as well as darkness, and the detector starts drawing boxes around nothing. Real systems face all of this at once.</p><p>You now know enough to question any claim built on underwater cameras. Read the <a href=\"#/learn/five\">five questions</a> below, try a <a href=\"#/observe\">live reef camera</a>, or start the course.</p>" }
  ];

  var MODULES = [
    { n: 1, title: "Images are arrays of numbers", depth: 0, time: "1.5 h", one: "Pixels, channels, cropping, and the two bugs everyone writes.",
      why: "Everything a computer “sees” is arithmetic on numbers. Most beginner mistakes in computer vision happen here, not in the models.",
      goals: ["Read an image’s shape and pick out any pixel’s colour.", "Crop a region with slicing, rows first.", "Split colour channels and read a histogram.", "Avoid swapped coordinates and 8-bit overflow."],
      lesson: ["A digital photo is a grid of tiny squares called pixels. Each stores three numbers: how much red, green and blue light reached that spot. A frame 640 pixels wide and 480 tall is, to a computer, a block of 480 × 640 × 3 = 921,600 numbers.",
        "Code addresses that block row first: <code>img[y, x]</code>, with row 0 at the top. A box around a fish, stored as <code>(x1, y1, x2, y2)</code>, is cut out with <code>img[y1:y2, x1:x2]</code>. Swapping x and y is the most common bug in student code, and it fails silently: you get a crop, just the wrong one.",
        "Files usually store each number as a whole number from 0 to 255. Arithmetic on those wraps around: 200 + 100 becomes 44. Convert to decimals between 0 and 1 before doing maths, and back at the end.",
        "<b>Try it:</b> click anywhere on the camera below to read the numbers behind that pixel. Fish pixels and water pixels differ most in the red channel."],
      demo: { type: "camera", preset: { dist: 1.5, water: "clear_ocean", light: 1, view: "camera", thr: 0.08 } },
      mistakes: ["Indexing <code>img[x, y]</code>. Arrays are rows first.", "Adding to 8-bit images and getting dark speckles where bright pixels wrapped past 255.", "Assuming every image is RGB. OpenCV loads channels as BGR, and some files carry a fourth transparency channel."],
      field: { t: "On the Live ocean page", b: "Pause any reef camera on the <a href=\"#/observe\">Live ocean</a> page. Every frame the detector analyses there is, first, a grid of numbers like this one." },
      nb: { file: "CV01_images_are_arrays.ipynb", inside: "The whole pipeline in about ten lines, then arrays, channels and histograms, cropping and drawing, data types, grayscale and hue. Two checked exercises.", run: "about 3 seconds" },
      quiz: [["An image has shape (480, 640, 3). How wide is it?", ["480 pixels", "640 pixels", "3 pixels"], 1, "Shape is height, width, channels."],
        ["A fish’s box is (x1, y1, x2, y2) = (10, 20, 50, 60). Which slice crops it?", ["img[10:50, 20:60]", "img[20:60, 10:50]", "img[10:20, 50:60]"], 1, "Rows (y) come first, then columns (x)."],
        ["In an 8-bit image, what does 200 + 100 give?", ["300", "255", "44"], 2, "It wraps around: 300 − 256 = 44. Convert to decimals first."]],
      further: [["Basic operations on images", "OpenCV tutorial", "https://docs.opencv.org/4.x/d3/df2/tutorial_py_basic_ops.html"], ["A crash course on NumPy for images", "scikit-image user guide", "https://scikit-image.org/docs/stable/user_guide/numpy_images.html"]] },

    { n: 2, title: "How water changes an image", depth: 3, time: "2 h", one: "The physics behind the missing fish: fading colour, haze and detection range.",
      why: "Murky water near an outfall changes what a camera can see, whatever is actually there. If you don’t account for it, the camera’s blindness can be mistaken for an ecological change.",
      goals: ["Write the image-formation model and explain each term.", "Compute how far away a fish can still be detected.", "Say what the project’s <code>degrade()</code> utility assumes and where it differs from physics.", "Explain why “restoring” a distant image mostly amplifies noise."],
      lesson: ["Light leaving a fish is absorbed and scattered on its way to the lens, separately for each colour. Red goes first; blue and green travel further. Particles also scatter daylight into the lens, adding a haze in the water’s own colour.",
        "<span class=\"lc-eq\">I = J · t + B · (1 − t), &nbsp; where t = e<sup>−β·d</sup> for each colour</span>",
        "<i>J</i> is the fish as it would look in air, <i>B</i> the colour of the haze, <i>β</i> how fast each colour fades per metre, and <i>d</i> the distance. As <i>d</i> grows, <i>t</i> shrinks and every pixel drifts toward <i>B</i>. Contrast disappears however bright the fish is.",
        "That gives every camera a <b>detection range</b>: the distance beyond which a fish no longer stands out. Murky water shortens it. In the notebook a colourful fish stays detectable to about 6 m in coastal water, a dark one to about 5 m.",
        "Undoing the haze means dividing by <i>t</i>. When <i>t</i> is tiny, sensor noise and 8-bit rounding are multiplied enormously, so the “restored” image is mostly amplified noise. Enhancement filters make frames easier to look at; they can’t bring back detail that fell below the noise."],
      demo: { type: "camera", preset: { dist: 6, water: "coastal", light: 1, view: "boxes", thr: 0.08 } },
      project: "From the project: a round-trip test of the image-formation model once failed at long range in murky water, because transmittance near 5 × 10<sup>−8</sup> amplified rounding about 20 million times. The fix was a conditioning table, not a looser tolerance.",
      mistakes: ["Treating fewer detections in murky water as fewer animals.", "Testing robustness with one artificial haze and calling the model robust.", "Believing an enhancement filter recovers information. It only changes how it’s displayed."],
      field: { t: "Seeing whales kilometres away", b: "Ships use thermal infrared cameras to spot whale blows, because a warm blow keeps its contrast against cold air at ranges where an ordinary camera sees only haze. One published system logged more than 4,500 blows at up to 5.5 km (Zitterbart and colleagues, <i>PLOS ONE</i>, 2013).", url: "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0071217" },
      nb: { file: "CV02_how_water_changes_images.ipynb", inside: "Fading curves for three water types, the same fish from 1 to 10 m, detection range, the project’s <code>degrade()</code> compared with the physics, restoration error, enhancement and noise, low light.", run: "about 3 seconds" },
      quiz: [["As distance grows, what does every pixel drift toward?", ["Black", "The colour of the water’s haze", "The fish’s true colour"], 1, "t shrinks, so the picture approaches B, the haze."],
        ["Which colour disappears first with distance in clear seawater?", ["Red", "Green", "Blue"], 0, "Water absorbs long red wavelengths fastest."],
        ["A colleague says an enhancement filter fixed the turbidity problem. What should you ask?", ["Which filter settings they used", "Whether detection rates were measured by turbidity after enhancement", "Whether the images were saved as PNG"], 1, "Enhancement changes appearance, not information. Only a measured detection rate answers the question."]],
      further: [["Sea-thru: removing water from underwater images", "Akkaynak and Treibitz, CVPR 2019", "https://openaccess.thecvf.com/content_CVPR_2019/html/Akkaynak_Sea-Thru_A_Method_for_Removing_Water_From_Underwater_Images_CVPR_2019_paper.html"]] },

    { n: 3, title: "Classical image processing", depth: 6, time: "2.5 h", one: "Filters, thresholds and shapes, and why touching fish break simple counts.",
      why: "These tools power the aquaculture segmentation baseline and many fish counters. They’re transparent and fast, and their failures are easy to see.",
      goals: ["Write a filter from scratch and choose kernels for blurring, sharpening and edges.", "Pick a threshold automatically with Otsu’s method.", "Clean a mask and split it into separate objects.", "Measure an object’s length and orientation."],
      lesson: ["A filter slides a small grid of weights, a <b>kernel</b>, over the image and replaces each pixel with a weighted sum of its neighbours. Equal weights blur; subtracting the left neighbours from the right finds vertical edges.",
        "To find fish: measure how far each pixel’s colour is from the background colour; keep pixels above a threshold (Otsu’s method picks one from the histogram); remove specks with morphological opening; then group touching pixels into objects, called connected components.",
        "Each object’s pixels form a cloud. Its main direction gives the fish’s orientation and its extent along that direction gives its length. In the notebook these lengths come out a few percent short, more for small distant fish, because edge pixels blend into the water.",
        "Fish that touch merge into one object. A distance transform plus watershed can split them, but loose settings split single fish too."],
      demo: { type: "filter" },
      mistakes: ["Looking for edges without blurring first, so every speck of noise becomes an edge.", "Using the mean of video frames as the background; passing fish drag it. Use the median.", "Reporting counts from connected components when fish overlap."],
      field: { t: "Counting salmon by sonar", b: "Sonar counters on salmon rivers rely on separating moving fish from a still background. The Caltech Fish Counting dataset collects such sonar video from rivers in Alaska and Washington to test newer methods.", url: "https://authors.library.caltech.edu/records/rbvyp-45b32" },
      nb: { file: "CV03_classical_image_processing.ipynb", inside: "Convolution from scratch, edges, Otsu from scratch, morphology, connected components, length measurement checked against the truth, watershed on touching fish, a median background from video.", run: "about 3 seconds" },
      quiz: [["Why blur an image before looking for edges?", ["Edges are easier to see in colour", "Edge kernels amplify noise; blurring suppresses it first", "Blurring makes the image smaller"], 1, "Edge kernels respond to every pixel-to-pixel jump, including noise."],
        ["Two touching fish come out as one object. Which tool can separate them?", ["Otsu’s threshold", "Distance transform plus watershed", "A stronger blur"], 1, "The distance transform has one peak per body; watershed grows a region from each."],
        ["For a fixed camera, why use the per-pixel median of many frames as the background?", ["It’s faster to compute", "Passing fish cover a pixel only briefly, so the median ignores them", "It removes colour"], 1, "The mean is pulled toward fish colours; the median isn’t."]],
      further: [["Image thresholding", "OpenCV tutorial", "https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html"], ["Gallery of examples", "scikit-image", "https://scikit-image.org/docs/stable/auto_examples/index.html"]] },

    { n: 4, title: "Learning to classify, honestly", depth: 10, time: "2.5 h", one: "A classifier from scratch, honest splits, the right metrics, and saying “I don’t know”.",
      why: "The monitoring workstream’s first model sorts frames into fish, other animal and empty. How you split and score it decides whether the reported number means anything.",
      goals: ["Train a classifier on hand-made features.", "Split video by clip, and show what goes wrong if you split by frame.", "Read a confusion matrix; compute precision, recall and F1.", "Add an abstention rule and read the coverage trade-off."],
      lesson: ["A classifier learns a rule from labelled examples. Here each frame is summarised by six numbers (foreground size, elongation, colour, edges) and a softmax model learns weights that turn them into probabilities for fish, non-fish and empty.",
        "Consecutive frames from one clip are near-copies. Put some in training and others in testing and the test becomes a memory test: in the notebook a nearest-neighbour model scores 0.90 that way and 0.54 when whole clips are kept apart. Split by clip, session, cage or site, never by frame.",
        "<b>Precision</b>: of the frames called fish, how many were. <b>Recall</b>: of the real fish frames, how many were found. On footage that is mostly empty water, a model that always answers “empty” scores 85% accuracy and finds no fish at all.",
        "Below a confidence threshold the model can answer “unknown” and send the frame to a person. Fewer frames are decided, but more of those are right."],
      demo: { type: "abstain" },
      mistakes: ["Splitting frames at random, so near-identical frames sit on both sides.", "Reporting accuracy on data that is mostly empty frames.", "Reading a model’s confidence as a calibrated probability without checking."],
      field: { t: "Reviewing fishing video faster", b: "NOAA’s Alaska Fisheries Science Center adapted YOLO detectors to find salmon in trawl-camera video, because reviewing footage by hand is among the largest costs of electronic monitoring.", url: "https://www.fisheries.noaa.gov/feature-story/faster-analysis-data-evaluate-bycatch-reduction-efforts-pollock-fishery" },
      nb: { file: "CV04_learning_to_classify.ipynb", inside: "The leakage demonstration, features, a softmax classifier from scratch compared with scikit-learn, the confusion matrix, the imbalance trap, abstention, and a reliability diagram.", run: "about 5 seconds" },
      quiz: [["A model scores 0.98 with a random frame split and 0.81 split by clip. Which do you report?", ["0.98", "0.81", "Their average"], 1, "The clip split is the honest estimate for a new camera visit."],
        ["Precision 0.95, recall 0.40. In plain words?", ["It finds most fish but raises many false alarms", "When it says “fish” it’s usually right, but it misses most fish", "It’s right 95% of the time overall"], 1, "Precision is about false alarms; recall is about misses."],
        ["Raising the confidence threshold usually…", ["raises coverage and accuracy", "lowers coverage and raises accuracy on the frames still decided", "leaves coverage unchanged"], 1, "More frames go to a person; the ones the model keeps are surer."]],
      further: [["Classification: accuracy, precision and recall", "Google Machine Learning Crash Course", "https://developers.google.com/machine-learning/crash-course/classification"], ["Metrics and scoring", "scikit-learn user guide", "https://scikit-learn.org/stable/modules/model_evaluation.html"]] },

    { n: 5, title: "Robustness and honest reporting", depth: 14, time: "2 h", one: "One number hides everything: report by condition and site, and say what the model must not do.",
      why: "The project’s cameras won’t sit in the clear water a public dataset came from. How a model behaves in murky, dark or unfamiliar water is the result that matters.",
      goals: ["Report results for each condition and site.", "Measure what happens in a habitat the model never saw.", "Use augmentation and say honestly what it fixed.", "Route unusable frames to a person; write data and model cards."],
      lesson: ["In the notebook the same model scores 0.93 on clean frames, between 0.45 and 0.80 under murk, low light and blur, and 0.55 on fish that are physically farther away. Trained only on reef clips, it drops to 0.71 in a harbour.",
        "Training on degraded copies (augmentation) recovers much of the loss from artificial haze, costs a little clean accuracy, and barely helps with the farther fish. Robustness to one kind of damage doesn’t transfer to another.",
        "A quality gate scores brightness, texture and sharpness on the frame’s border, where there’s usually only background, so it judges the image and not the animal. Frames it flags become “unknown” and go to a person, never to a “safe” default.",
        "Every model should ship with a data card (where the data came from, its licence, its gaps) and a model card. The most important field on the model card is “must not be used for”."],
      demo: { type: "conditions" },
      mistakes: ["Publishing one overall accuracy.", "Augmenting with the same distortion you test with, then claiming robustness.", "Letting poor-quality frames default to “no animals present”."],
      field: { t: "A person checks before the alert", b: "In a 2026 whale-detection system in San Francisco Bay, thermal cameras flag possible whales and a trained specialist confirms each one before ships are alerted.", url: "https://news.ucsb.edu/2026/022586/new-ai-system-uses-cameras-and-thermal-sensors-steer-ships-clear-gray-whales-san" },
      nb: { file: "CV05_robustness_and_reporting.ipynb", inside: "Accuracy by condition, a habitat-shift table, augmentation, an image-quality gate, an error taxonomy, data and model cards, and conservative event records.", run: "about 9 seconds" },
      quiz: [["Accuracy is 0.95 overall and 0.55 in turbid water. What’s the honest headline?", ["0.95", "Both numbers, with the condition named", "0.55"], 1, "The overall number alone misleads anyone deploying where turbidity is common."],
        ["A frame is degraded and the model is 62% sure it’s empty. What should the record say?", ["Empty, no animals", "Unknown, human review required", "Delete the frame"], 1, "Weak evidence never defaults to a safe state."],
        ["Training with artificial haze lifted haze accuracy a lot. Does that prove robustness to real murky water?", ["Yes", "No; test with a different degradation model and real footage"], 1, "A model can learn to undo one specific distortion without coping with the real thing."]],
      further: [["Model cards for model reporting", "Mitchell and colleagues, 2019", "https://arxiv.org/abs/1810.03993"], ["Datasheets for datasets", "Gebru and colleagues, 2018", "https://arxiv.org/abs/1803.09010"]] },

    { n: 6, title: "Neural networks and CNNs", depth: 18, time: "2.5 h", one: "A model that learns its own filters, what it looks at, and a robustness test that can mislead.",
      why: "The monitoring workstream’s upgrade is a convolutional network fine-tuned on real footage. You need to know what it adds, what it costs, and how to test it fairly.",
      goals: ["Train a linear model, a small fully connected network and a small CNN, and compare them by condition.", "Look inside: learned filters, feature maps and a saliency map.", "Fine-tune a pretrained network on your own frames."],
      lesson: ["A convolutional neural network (CNN) learns its own filters: the same small kernels as Module 03, but with weights found by training. Each filter is reused at every position, so a fish in the corner and a fish in the centre are detected by the same weights.",
        "In the notebook a small CNN beats a fully connected network with nearly 40 times more parameters. One preprocessing line, standardising each frame by its own average and spread, lifts its clean accuracy from about 0.78 to 0.93.",
        "That same line lifts accuracy under the project’s artificial haze and darkness to between 0.93 and 0.99, because those distortions mostly scale and shift the whole frame, which standardising cancels. On fish that are physically farther away it stays near 0.7. <b>A near-perfect score under one degradation model can hide a large gap under another.</b>",
        "Pretrained networks have already learned edges and textures from millions of photos. Replacing their last layer and training briefly on your frames, called transfer learning, is the practical route with small datasets."],
      demo: { type: "cnn" },
      mistakes: ["Trusting a robustness score from a single artificial distortion.", "Skipping the saliency check: a model that looks at the background has learned a shortcut.", "Fine-tuning every layer of a large pretrained network on a few hundred frames."],
      field: { t: "A detector in your browser", b: "The <a href=\"#/observe\">Live ocean</a> page runs YOLOv8n, a compact detection network, in your browser on live reef video. Before trusting what any detector reports, check what it was trained to recognise (Module 07)." },
      nb: { file: "CV06_neural_networks_and_cnns.ipynb", inside: "PyTorch tensors, three models compared by condition, per-image normalisation, learned filters and feature maps, saliency, augmentation, size and speed, and a tested transfer-learning function.", run: "about a minute" },
      quiz: [["Why does a CNN need far fewer parameters than a fully connected network on raw pixels?", ["It uses smaller images", "Its filters are reused at every position", "It ignores colour"], 1, "Weight sharing: one small filter scans the whole image."],
        ["A saliency map lights up the background, not the fish. What might be wrong?", ["Nothing", "The model learned a shortcut from the background", "The image is too small"], 1, "Check whether background or habitat correlates with the label in your training data."],
        ["Why freeze a pretrained network’s early layers at first?", ["They hold general features; training only the new layer is faster and less likely to overfit", "Frozen layers run on the GPU", "It improves colour accuracy"], 0, "Early layers detect edges and textures that transfer well."]],
      further: [["Training a classifier", "PyTorch tutorial", "https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html"], ["Community computer vision course", "Hugging Face", "https://huggingface.co/learn/computer-vision-course"], ["Practical deep learning", "fast.ai", "https://course.fast.ai/"]] },

    { n: 7, title: "Detection, measurement and calibration", depth: 23, time: "2.5 h", one: "Where is the fish, how long is it, how heavy, and how wrong could each answer be?",
      why: "Aquaculture growth and welfare evidence rests on lengths and weights estimated from images. Small measurement biases become large weight errors, and a badly built metric can look fine while carrying no information.",
      goals: ["Score boxes with IoU, remove duplicates, and compute average precision.", "Convert pixels to centimetres, and say why the scale depends on distance.", "Quantify the size bias of a flat underwater camera window.", "Carry length error into weight error, and spot a circular welfare metric."],
      lesson: ["A detector draws boxes. A box counts as correct if it overlaps a true box enough: <b>intersection over union</b> (IoU) of at least 0.5 is the usual rule. Average precision (AP) sums up how precision and recall trade off as the confidence threshold moves.",
        "In the notebook the same detector scores AP 0.99 in clear water, 0.71 in coastal water and 0.25 in a murky harbour, where its recall never rises above about a quarter. No threshold finds fish that never produced a detection.",
        "Pixels aren’t centimetres. A fish’s size in the image depends on its distance. Behind a flat underwater window, light bends as it leaves the water, so fish look about 1.33 times larger than an in-air calibration expects, and more toward the edges of the frame.",
        "Weight is usually estimated from length as <i>W = a·L<sup>b</sup></i>, with <i>b</i> near 3. So a 5% length error becomes roughly a 15% weight error.",
        "Fulton’s condition factor <i>K</i> = 100·<i>W</i>/<i>L</i><sup>3</sup> flags thin fish. But if <i>W</i> was itself estimated from <i>L</i>, then <i>K</i> = 100·<i>a</i>·<i>L</i><sup><i>b</i>−3</sup>: with <i>b</i> = 3, every fish gets the same <i>K</i>, however thin or fat it really is."],
      demo: { type: "port" },
      project: "For Capstone B: the aquaculture notebook estimates weight from length, then computes the condition factor from that weight. Every fish gets K = 1.20, the exact lower edge of its placeholder band, so the welfare flag can’t respond to a thin fish. Module 07’s notebook shows why, and an image-based alternative to validate against weighed fish.",
      mistakes: ["Calibrating a camera in air and using it behind a flat port.", "Computing a welfare metric from numbers that were derived from each other.", "Assuming an off-the-shelf detector knows what a fish is: COCO, the most common training set, has no fish class."],
      field: { t: "Counting catch on fishing vessels", b: "Electronic monitoring counts and measures catch from deck video. An industry trial combining a neural network with a tracker produced automatic counts close to manual counts for target species (<i>Canadian Journal of Fisheries and Aquatic Sciences</i>, 2021).", url: "https://cdnsciencepub.com/doi/10.1139/cjfas-2020-0446" },
      nb: { file: "CV07_detection_measurement_calibration.ipynb", inside: "IoU, box formats, non-maximum suppression, precision–recall and AP in three waters, COCO’s missing fish class, pixel scale and distance, flat-port refraction, length-to-weight error, the condition-factor problem, a bootstrap biomass interval.", run: "about 5 seconds" },
      quiz: [["Two equal boxes overlap by half their width. What is their IoU?", ["1/2", "1/3", "1/4"], 1, "The overlap is half a box; the union is one and a half boxes."],
        ["A camera calibrated in air is used behind a flat port. Fish lengths come out…", ["too small", "too big, by about a third at the centre", "unchanged"], 1, "Refraction magnifies by roughly the water’s refractive index, 1.33, and more off-axis."],
        ["If W = a·L³, a 5% length error gives roughly what weight error?", ["5%", "10%", "15%"], 2, "Relative error multiplies by the exponent: about 3 × 5%."]],
      further: [["Detection evaluation", "COCO", "https://cocodataset.org/#detection-eval"], ["Camera calibration", "OpenCV tutorial", "https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html"], ["Length–weight parameters by species", "FishBase", "https://www.fishbase.se"]] },

    { n: 8, title: "Tracking over time", depth: 28, time: "2.5 h", one: "Following individual fish across frames, and what the camera rig must guarantee.",
      why: "Counts, swimming behaviour and school cohesion all come from tracks. A tracker that splits one fish into five tracks inflates counts and corrupts every behaviour metric built on it.",
      goals: ["Build a Kalman filter that coasts through missed detections.", "Match detections to tracks with the Hungarian algorithm and a gate.", "Report tracks per fish, ID switches and track purity.", "Turn a tracking failure into a camera requirement."],
      lesson: ["Tracking by detection means detecting in every frame, then linking detections into tracks. A <b>Kalman filter</b> keeps each fish’s position and velocity, predicts where it should be next, and blends that prediction with the new detection, trusting whichever is less uncertain. With no detection, it coasts on the prediction.",
        "The <b>Hungarian algorithm</b> pairs predictions with detections so the total distance is smallest. A gate forbids pairs that are too far apart. Tracks are confirmed after a few matches and deleted after too many misses.",
        "In the notebook’s simulation, 12 fish give 12 tracks when each moves less than a tenth of the distance to its nearest neighbour between frames, 32 tracks at about a quarter, and 60 at about half. Frame rate and field of view are rig requirements, not tuning knobs."],
      demo: { type: "kalman" },
      project: "From the project: a tracker once produced 205 tracks for 12 fish because simulated fish moved about 34 pixels per frame in a 37 cm field of view. It was documented as a camera requirement rather than tuned away.",
      mistakes: ["Tuning the tracker to hide a frame-rate problem.", "Deleting tracks too quickly, so every occlusion creates a “new” fish.", "Assuming smoother velocities always give better behaviour metrics."],
      field: { t: "Counting fish through a gate", b: "Counting fish that pass a fishway or a net opening is a tracking problem: each fish must be counted once, however long it lingers. Sonar and video counters on rivers work this way, and their errors come mostly from crossings and occlusions." },
      nb: { file: "CV08_tracking_over_time.ipynb", inside: "A simulated school, a single-fish Kalman demo, a multi-fish tracker, tuning the gate and track lifetime, a camera-siting sweep, school polarisation from raw and Kalman velocities, line-crossing counts.", run: "about 3 seconds" },
      quiz: [["In a frame with no detection, a Kalman filter…", ["deletes the track", "predicts and coasts, with growing uncertainty", "copies the last detection"], 1, "Prediction continues; the update step is skipped."],
        ["A tracker reports 40 tracks for 10 fish. A likely cause?", ["Fish move too far between frames for the gate", "The fish are too colourful", "The video is in colour"], 0, "Raise the frame rate or widen the field of view; then check the gate and track lifetime."],
        ["Why gate the assignment?", ["To save memory", "So a track can’t pair with a distant false detection", "To speed up the filter"], 1, "Without a gate the algorithm always pairs something."]],
      further: [["Simple online and realtime tracking (SORT)", "Bewley and colleagues, 2016", "https://arxiv.org/abs/1602.00763"], ["Kalman and Bayesian filters in Python", "Roger Labbe, free book", "https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python"]] },

    { n: 9, title: "From pixels to defensible claims", depth: 34, time: "2 h", one: "Why fewer detections near an outfall doesn’t mean fewer fish, and how to write what the evidence supports.",
      why: "This is where camera results meet permits and policy. Every path through the course ends here.",
      goals: ["Separate occupancy (is the animal there?) from detection (would the camera see it?).", "Explain false alarms and a survey’s power.", "Write a finding that states what it does and doesn’t show.", "Name the welfare, surveillance and licensing questions that come with the camera."],
      lesson: ["<b>Occupancy</b> asks whether an animal uses a site. <b>Detection probability</b> asks whether the camera would see it if it did. Raw counts mix the two.",
        "In the notebook’s simulated survey the outfall has no effect on fish at all, yet visits near it record a detection 41% less often, because the water there is murkier. Read naively, that is an impact that doesn’t exist.",
        "Visiting each site several times reveals how often a fish that is present gets missed. An occupancy model (MacKenzie and colleagues, 2002) uses those repeat visits to estimate presence and detection separately. Across 20 simulated surveys with no real impact, the naive comparison reported an impact 95% of the time and the model never did. When occupancy at the outfall really fell from 0.6 to 0.25, the model caught it in about a third of surveys: “no detectable effect” means little without the survey’s power.",
        "The model only works because murkiness changes from visit to visit with weather and tide. If it depended on distance alone, nothing could separate it from a real effect. Survey design decides what can be known."],
      demo: { type: "occ" },
      extra: "<h3>Responsibilities that come with the camera</h3><ul><li><b>Sentience.</b> The UK’s Animal Welfare (Sentience) Act 2022, an enacted law, recognises vertebrates (fish included), decapod crustaceans and cephalopod molluscs as sentient for the purposes of that Act, following a 2021 evidence review led by Jonathan Birch at LSE. A model’s welfare flag is a reason for a person to look, never a diagnosis.</li><li><b>The rig can change the result.</b> Lights, noise and equipment can change animal behaviour. Record the setup.</li><li><b>Surveillance.</b> Tracking that counts fish can also follow people on a deck or a shore. Ask who is recorded, whether they know, and how long footage is kept.</li><li><b>Licences.</b> Record each dataset’s and tool’s licence. Ultralytics YOLO is AGPL-3.0, which also covers models trained with it.</li><li><b>Policy accuracy.</b> When findings are cited, keep enacted law, proposed bills and guidance clearly apart.</li></ul>",
      mistakes: ["Reading fewer detections as fewer animals.", "Reporting “no effect” without the survey’s power.", "Letting a model’s welfare flag stand in for a diagnosis."],
      field: { t: "Where camera evidence meets permits", b: "Permits for thermal discharge increasingly rely on monitoring. The <a href=\"#/officials\">For officials</a> toolkit shows where camera evidence enters those instruments, and what conditions to attach." },
      nb: { file: "CV09_from_pixels_to_claims.ipynb", inside: "A world with no impact, the naive analysis, an occupancy model fitted by maximum likelihood, false alarms and power over 20 surveys, and a finding written automatically from the fitted numbers.", run: "about 5 seconds" },
      quiz: [["Detections fall by half near an outfall. Which claim can the counts alone not support?", ["Murkier water may lower detection", "Fish may avoid the camera’s view", "The outfall reduced the fish population"], 2, "Without separating detection from presence, the counts can’t say why they fell."],
        ["Why do repeat visits make detection probability estimable?", ["They average out noise", "At occupied sites, the pattern of hits and misses shows how often a present fish is missed", "They increase the sample size"], 1, "A site with detections on some visits and not others is occupied but imperfectly seen."],
        ["The interval for the outfall effect runs from −1.4 to +2.1. What can you say?", ["There is an impact", "There is no impact", "The survey can’t distinguish no effect from a negative or positive one"], 2, "More sites, more visits or better detection would narrow it."]],
      further: [["Estimating site occupancy rates when detection is imperfect", "MacKenzie and colleagues, Ecology, 2002", "https://doi.org/10.1890/0012-9658(2002)083[2248:ESORWD]2.0.CO;2"], ["Animal Welfare (Sentience) Act 2022", "legislation.gov.uk", "https://www.legislation.gov.uk/ukpga/2022/22"], ["Review of the evidence of sentience in cephalopods and decapods", "LSE, 2021", "https://www.lse.ac.uk/business/consulting/reports/review-of-the-evidence-of-sentiences-in-cephalopod-molluscs-and-decapod-crustaceans"]] }
  ];

  var GLOSSARY = [
    ["Abstention", "Answering “unknown” when the model isn’t confident enough, so a person reviews the frame.", 4],
    ["Augmentation", "Training on altered copies of images (darker, hazier, blurred) so a model sees more conditions.", 5],
    ["Average precision (AP)", "One number summarising how a detector trades false alarms against misses.", 7],
    ["Backscatter", "Haze from light scattered toward the camera by particles in the water.", 2],
    ["Bounding box", "The rectangle a detector draws around an object it found.", 7],
    ["Channel", "One of the three colour layers of an image: red, green or blue.", 1],
    ["Classifier", "A model that sorts each input into a category, such as fish, other animal or empty.", 4],
    ["CNN", "Convolutional neural network: a model that learns small filters and slides them over the image.", 6],
    ["Confusion matrix", "A table of what the model predicted against what was true, showing which mistakes it makes.", 4],
    ["Data leakage", "When test data shares information with training data, such as frames from the same clip, so scores look better than they are.", 4],
    ["Detection probability", "The chance a camera detects an animal on a visit, given the animal is there.", 9],
    ["Detection range", "The distance beyond which a fish no longer stands out from the water.", 2],
    ["Filter (kernel)", "A small grid of weights slid over an image to blur, sharpen or find edges.", 3],
    ["ID switch", "A tracking error where one animal’s track jumps to another animal.", 8],
    ["IoU", "Intersection over union: how much two boxes overlap, from 0 (not at all) to 1 (exactly).", 7],
    ["Kalman filter", "A method that predicts where an object will be next and blends that with each new measurement.", 8],
    ["Model card", "A short document stating what a model was trained on, how it performs, and what it must not be used for.", 5],
    ["Occupancy", "Whether a species uses a site, as distinct from whether it was detected there.", 9],
    ["Pixel", "One tiny square of an image, holding a colour as numbers.", 1],
    ["Power", "The chance a survey detects an effect that really exists.", 9],
    ["Precision", "Of the things the model called fish, the share that really were.", 4],
    ["Recall", "Of the real fish, the share the model found.", 4],
    ["Threshold", "A cut-off value: above it counts as yes, below as no.", 3],
    ["Transfer learning", "Starting from a network trained on other images and retraining only its last part on yours.", 6],
    ["Transmittance", "The fraction of light of each colour that survives a given distance of water.", 2]
  ];

  /* ============================== ENGINE ============================== */
  var U = window.AGU, standalone = !U;
  if (standalone) U = { inits: {}, onRoute: {} };
  U.onRoute = U.onRoute || {};
  var root, booted = false, tourApi = null, current = null;
  var state = { path: "all", done: {}, quiz: {} };
  var CK = { bg: "#021017", line: "#1A3a46", muted: "#8AA7B0", ink: "#DCEAEE", glow: "#F7B24A", ice: "#9ED8E6", warn: "#FF8E6E", good: "#7FE0B0" };
  var WATER = {
    clear_ocean: { label: "Clear ocean", beta: [0.40, 0.07, 0.04], veil: [0.02, 0.20, 0.42] },
    coastal: { label: "Coastal", beta: [0.55, 0.20, 0.30], veil: [0.05, 0.32, 0.27] },
    turbid_harbour: { label: "Murky harbour", beta: [0.95, 0.60, 0.75], veil: [0.14, 0.30, 0.22] }
  };
  var ORANGE = [0.97, 0.55, 0.12];

  function q(s, r) { return (r || root).querySelector(s); }
  function qa(s, r) { return Array.prototype.slice.call((r || root).querySelectorAll(s)); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function pct(x) { return Math.round(100 * x) + "%"; }
  function expit(x) { return 1 / (1 + Math.exp(-x)); }
  function save(k, v) { try { localStorage.setItem("agl-" + k, JSON.stringify(v)); } catch (e) {} }
  function load(k, d) { try { var v = localStorage.getItem("agl-" + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function rng(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function gauss(r) { var u = 0, v = 0; while (!u) u = r(); while (!v) v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
  function seen(J, d, w) { var W = WATER[w]; return J.map(function (j, c) { var t = Math.exp(-W.beta[c] * d); return j * t + W.veil[c] * (1 - t); }); }
  function css(c) { return "rgb(" + c.map(function (v) { return Math.round(255 * Math.max(0, Math.min(1, v))); }).join(",") + ")"; }
  function hidpi(cv, responsive) {
    if (!cv.dataset.w) { cv.dataset.w = cv.getAttribute("width"); cv.dataset.h = cv.getAttribute("height"); }
    var w = +cv.dataset.w, h = +cv.dataset.h, shown = cv.clientWidth || w;
    if (responsive) w = Math.max(300, Math.round(shown));
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = w * dpr; cv.height = h * dpr;
    var g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
    var fs = responsive ? 12 : Math.min(22, 12 * w / Math.max(shown, 1));
    g.font = fs.toFixed(1) + "px " + (getComputedStyle(document.body).fontFamily || "sans-serif");
    return { g: g, w: w, h: h, fs: fs };
  }
  function seg(name, opts, value) {
    return '<div class="seg" role="group" aria-label="' + esc(name) + '">' + opts.map(function (o) {
      return '<button type="button" data-v="' + o[0] + '" aria-pressed="' + (o[0] === value) + '">' + o[1] + "</button>";
    }).join("") + "</div>";
  }
  function bindSeg(el, fn) {
    qa("button", el).forEach(function (b) { b.addEventListener("click", function () { qa("button", el).forEach(function (x) { x.setAttribute("aria-pressed", x === b); }); fn(b.dataset.v); }); });
  }
  function setSeg(el, v) { qa("button", el).forEach(function (x) { x.setAttribute("aria-pressed", x.dataset.v === String(v)); }); }
  function range(id, label, min, max, step, val) {
    return '<div class="ctl"><label for="' + id + '">' + label + ' <output id="' + id + '-o"></output></label><input type="range" id="' + id + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + val + '"></div>';
  }
  function inst(title, tag, view, ctrl, finding) {
    return '<div class="inst"><div class="inst-head"><h3>' + title + '</h3><span class="tag">' + tag + '</span></div><div class="inst-body"><div class="inst-view">' + view + '</div><div class="inst-ctrl">' + ctrl + "</div></div>" + (finding ? '<p class="finding" aria-live="polite"></p>' : "") + "</div>";
  }
  var uid = 0;

  /* ---------------- shared synthetic scene ---------------- */
  var SCENE = null;
  function scene() {
    if (SCENE) return SCENE;
    var W = 360, H = 216, N = W * H, r = rng(7), J = new Float32Array(N * 3), idx = new Int8Array(N).fill(-1), noise = new Float32Array(N * 3), M = Math.max(W, H);
    var FISH = [
      { cx: 70, cy: 62, L: 74, ang: 0.15, col: [0.97, 0.55, 0.12], f: 0.6 },
      { cx: 192, cy: 44, L: 62, ang: Math.PI - 0.2, col: [0.96, 0.84, 0.22], f: 0.8 },
      { cx: 292, cy: 92, L: 68, ang: 0.3, col: [0.80, 0.82, 0.84], f: 1.0 },
      { cx: 122, cy: 152, L: 76, ang: Math.PI + 0.1, col: [0.93, 0.35, 0.25], f: 1.25 },
      { cx: 256, cy: 174, L: 62, ang: -0.25, col: [0.97, 0.55, 0.12], f: 1.5 }];
    for (var y = 0; y < H; y++) for (var x = 0; x < W; x++) {
      var i = y * W + x, n1 = gauss(r);
      J[3 * i] = 0.48 + 0.10 * y / M + 0.04 * n1 + 0.015 * gauss(r);
      J[3 * i + 1] = 0.43 + 0.08 * y / M + 0.04 * n1 + 0.015 * gauss(r);
      J[3 * i + 2] = 0.34 + 0.04 * x / M + 0.04 * n1 + 0.015 * gauss(r);
      for (var c = 0; c < 3; c++) noise[3 * i + c] = gauss(r);
    }
    FISH.forEach(function (F, k) {
      var a = F.L / 2.25, b = a / 4, ca = Math.cos(F.ang), sa = Math.sin(F.ang);
      for (var y = Math.max(0, F.cy - F.L); y < Math.min(H, F.cy + F.L); y++) for (var x = Math.max(0, F.cx - F.L); x < Math.min(W, F.cx + F.L); x++) {
        var X = (x - F.cx) * ca + (y - F.cy) * sa, Y = -(x - F.cx) * sa + (y - F.cy) * ca;
        var body = (X / a) * (X / a) + (Y / b) * (Y / b) <= 1, tx = -X - 0.8 * a;
        var tail = tx >= 0 && tx <= 0.45 * a && Math.abs(Y) <= 1.3 * b * tx / (0.45 * a);
        if (!body && !tail) continue;
        var i = y * W + x, col = F.col;
        if (body && Math.abs(X - 0.15 * a) < 0.09 * a) col = [0.95, 0.95, 0.92];
        if (Math.pow(X - 0.62 * a, 2) + Math.pow(Y - 0.15 * b, 2) < Math.pow(0.12 * b + 0.6, 2)) col = [0.05, 0.05, 0.08];
        J[3 * i] = col[0]; J[3 * i + 1] = col[1]; J[3 * i + 2] = col[2]; idx[i] = k;
      }
    });
    SCENE = { W: W, H: H, N: N, J: J, idx: idx, noise: noise, FISH: FISH };
    return SCENE;
  }
  function renderScene(S, p, I) {   // fills I (Float32Array N*3) for preset p, returns transmittances
    var Wt = WATER[p.water], sd = 0.012 / Math.sqrt(p.light), T = [];
    for (var k = 0; k <= 5; k++) { var d = k < 5 ? p.dist * S.FISH[k].f : p.dist + 8; T.push(Wt.beta.map(function (be) { return Math.exp(-be * d); })); }
    for (var i = 0; i < S.N; i++) {
      var t = T[S.idx[i] < 0 ? 5 : S.idx[i]];
      for (var c = 0; c < 3; c++) { var v = S.J[3 * i + c] * t[c] + Wt.veil[c] * (1 - t[c]) + sd * S.noise[3 * i + c]; I[3 * i + c] = v < 0 ? 0 : v > 1 ? 1 : v; }
    }
    return T;
  }

  /* ---------------- instrument: underwater camera ---------------- */
  function mountCamera(host, preset) {
    var id = "cam" + (++uid), S = scene(), W = S.W, H = S.H, N = S.N;
    var p = Object.assign({ dist: 3, water: "coastal", light: 1, view: "boxes", thr: 0.08 }, preset || {});
    var view = '<div class="lc-canvas-wrap"><canvas width="360" height="216" id="' + id + '-cv" role="img"></canvas><div class="lc-pixel" id="' + id + '-px" hidden></div></div>' +
      '<div class="readouts"><div class="ro hot"><b id="' + id + '-found"></b><span>fish found by the detector</span></div><div class="ro"><b id="' + id + '-false"></b><span>false boxes</span></div><div class="ro"><b id="' + id + '-range"></b><span>how far it could see this fish type</span></div></div>';
    var ctrl = '<span class="lc-ctl-label">What to show</span>' + seg("View", [["camera", "Picture"], ["diff", "Difference"], ["mask", "Mask"], ["boxes", "Boxes"]], p.view) +
      '<div style="height:.9rem"></div>' + range(id + "-d", "Distance to the fish", 0.5, 15, 0.1, p.dist) +
      '<span class="lc-ctl-label">Water</span>' + seg("Water", [["clear_ocean", "Clear ocean"], ["coastal", "Coastal"], ["turbid_harbour", "Murky harbour"]], p.water) +
      '<div style="height:.9rem"></div>' + range(id + "-l", "Daylight", 0.06, 1, 0.01, p.light) + range(id + "-t", "Difference needed to count as fish", 0.03, 0.2, 0.005, p.thr) +
      '<div class="lc-chbars" aria-label="Share of each colour reaching the lens from the middle fish"><span>Red</span><span class="t"><i id="' + id + '-r" style="background:#FF7A6B"></i></span><span class="v" id="' + id + '-rv"></span><span>Green</span><span class="t"><i id="' + id + '-g" style="background:#6FD39A"></i></span><span class="v" id="' + id + '-gv"></span><span>Blue</span><span class="t"><i id="' + id + '-b" style="background:#7EA6EC"></i></span><span class="v" id="' + id + '-bv"></span></div>' +
      '<p class="small" style="color:var(--deep-muted);margin:.7rem 0 0">Colour reaching the lens from the middle fish. Synthetic scene; teaching values for the water.</p>';
    host.innerHTML = inst("Underwater camera", "tap the picture to read a pixel", view, ctrl, true);
    var cv = q("#" + id + "-cv", host), g = cv.getContext("2d"), img = g.createImageData(W, H);
    var I = new Float32Array(N * 3), diff = new Float32Array(N), mask = new Uint8Array(N), clean = new Uint8Array(N), lab = new Int32Array(N), stack = new Int32Array(N);
    var segs = qa(".seg", host), pending = false;
    function detect() {
      var bg = [0, 1, 2].map(function (c) {
        var a = [], x, y;
        for (x = 0; x < W; x += 2) [0, 2, H - 3, H - 1].forEach(function (yy) { a.push(I[3 * (yy * W + x) + c]); });
        for (y = 4; y < H - 4; y += 2) [0, 2, W - 3, W - 1].forEach(function (xx) { a.push(I[3 * (y * W + xx) + c]); });
        a.sort(function (u, v) { return u - v; }); return a[a.length >> 1];
      });
      for (var i = 0; i < N; i++) { var dr = I[3 * i] - bg[0], dg = I[3 * i + 1] - bg[1], db = I[3 * i + 2] - bg[2]; diff[i] = Math.sqrt(dr * dr + dg * dg + db * db); mask[i] = diff[i] > p.thr ? 1 : 0; }
      clean.fill(0);
      for (var y = 1; y < H - 1; y++) for (var x = 1; x < W - 1; x++) { var s = 0; for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) s += mask[(y + dy) * W + x + dx]; clean[y * W + x] = s >= 5 ? 1 : 0; }
      lab.fill(0); var boxes = [], cur = 0;
      for (var s0 = 0; s0 < N; s0++) {
        if (!clean[s0] || lab[s0]) continue;
        cur++; var sp = 0, area = 0, x1 = W, y1 = H, x2 = 0, y2 = 0; stack[sp++] = s0; lab[s0] = cur;
        while (sp) {
          var pp = stack[--sp], px = pp % W, py = (pp - px) / W; area++;
          if (px < x1) x1 = px; if (px > x2) x2 = px; if (py < y1) y1 = py; if (py > y2) y2 = py;
          if (px > 0 && clean[pp - 1] && !lab[pp - 1]) { lab[pp - 1] = cur; stack[sp++] = pp - 1; }
          if (px < W - 1 && clean[pp + 1] && !lab[pp + 1]) { lab[pp + 1] = cur; stack[sp++] = pp + 1; }
          if (py > 0 && clean[pp - W] && !lab[pp - W]) { lab[pp - W] = cur; stack[sp++] = pp - W; }
          if (py < H - 1 && clean[pp + W] && !lab[pp + W]) { lab[pp + W] = cur; stack[sp++] = pp + W; }
        }
        if (area >= 40) boxes.push([x1, y1, x2 + 1, y2 + 1]);
      }
      return { bg: bg, boxes: boxes };
    }
    function rangeFor(fishK) {   // farthest distance at which this fish's mean colour still differs enough from the water behind it
      var F = S.FISH[fishK], Wt = WATER[p.water], bgJ = [0.52, 0.47, 0.36];
      for (var d = 0.5; d <= 30; d += 0.1) {
        var a = seen(F.col, d, p.water), b = seen(bgJ, d + 8, p.water);
        if (Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]) <= p.thr) return d;
      }
      return 30;
    }
    function draw() {
      pending = false;
      var T = renderScene(S, p, I), det = detect(), i, v;
      for (i = 0; i < N; i++) {
        var o = 4 * i;
        if (p.view === "diff") { v = Math.min(1, diff[i] / 0.35); img.data[o] = 255 * Math.min(1, v * 1.4); img.data[o + 1] = 255 * v * 0.85; img.data[o + 2] = 255 * (0.25 + 0.4 * v); }
        else if (p.view === "mask") { v = clean[i] ? 235 : 12; img.data[o] = v; img.data[o + 1] = clean[i] ? 225 : 28; img.data[o + 2] = clean[i] ? 200 : 36; }
        else { img.data[o] = 255 * I[3 * i]; img.data[o + 1] = 255 * I[3 * i + 1]; img.data[o + 2] = 255 * I[3 * i + 2]; }
        img.data[o + 3] = 255;
      }
      g.putImageData(img, 0, 0);
      if (p.view === "boxes" || p.view === "mask") { g.lineWidth = 2; g.strokeStyle = CK.glow; det.boxes.forEach(function (b) { g.strokeRect(b[0] + 0.5, b[1] + 0.5, b[2] - b[0] - 1, b[3] - b[1] - 1); }); }
      var inBox = function (F, b) { return F.cx >= b[0] && F.cx <= b[2] && F.cy >= b[1] && F.cy <= b[3]; };
      var found = S.FISH.filter(function (F) { return det.boxes.some(function (b) { return inBox(F, b); }); }).length;
      var fb = det.boxes.filter(function (b) { return !S.FISH.some(function (F) { return inBox(F, b); }); }).length;
      q("#" + id + "-found", host).textContent = found + " of 5";
      q("#" + id + "-false", host).textContent = fb;
      var rg = rangeFor(2); q("#" + id + "-range", host).textContent = rg >= 30 ? "30+ m" : rg.toFixed(1) + " m";
      q("#" + id + "-d-o", host).textContent = p.dist.toFixed(1) + " m";
      q("#" + id + "-l-o", host).textContent = p.light >= 0.8 ? "full sun" : p.light >= 0.35 ? "overcast" : p.light >= 0.15 ? "dusk" : "near dark";
      q("#" + id + "-t-o", host).textContent = p.thr.toFixed(3);
      ["r", "g", "b"].forEach(function (ch, c) { q("#" + id + "-" + ch, host).style.width = (100 * T[2][c]).toFixed(1) + "%"; q("#" + id + "-" + ch + "v", host).textContent = pct(T[2][c]); });
      var f = q(".finding", host);
      f.innerHTML = found < 5 ? "<b>" + (5 - found) + " of 5 fish missed.</b> All five are still in the scene; the camera just can’t separate them from the water." + (fb ? " Noise is also producing false boxes." : "")
        : fb ? "<b>All five found, plus " + fb + " false " + (fb === 1 ? "box" : "boxes") + ".</b> A lower threshold catches more fish and more noise." : "<b>All five fish found.</b> Try moving them farther away, or switch to murky water.";
      cv.setAttribute("aria-label", "Synthetic underwater frame, five fish about " + p.dist.toFixed(1) + " metres away in " + WATER[p.water].label.toLowerCase() + " water. Detector finds " + found + " of 5.");
    }
    function later() { if (!pending) { pending = true; requestAnimationFrame(draw); } }
    bindSeg(segs[0], function (v) { p.view = v; later(); });
    bindSeg(segs[1], function (v) { p.water = v; later(); });
    [["-d", "dist"], ["-l", "light"], ["-t", "thr"]].forEach(function (a) { q("#" + id + a[0], host).addEventListener("input", function (e) { p[a[1]] = +e.target.value; later(); }); });
    function inspect(ev) {
      var r = cv.getBoundingClientRect(), x = Math.floor((ev.clientX - r.left) / r.width * W), y = Math.floor((ev.clientY - r.top) / r.height * H);
      if (x < 0 || y < 0 || x >= W || y >= H) return;
      var i = y * W + x, c = [I[3 * i], I[3 * i + 1], I[3 * i + 2]].map(function (v) { return Math.round(255 * v); });
      var px = q("#" + id + "-px", host); px.hidden = false;
      px.innerHTML = '<span class="sw" style="background:rgb(' + c.join(",") + ')"></span>Row ' + y + ", column " + x + "<br>Red " + c[0] + ", green " + c[1] + ", blue " + c[2] + "<br>" + (S.idx[i] >= 0 ? "a fish pixel" : "water and reef behind");
    }
    cv.addEventListener("pointerdown", inspect);
    cv.addEventListener("pointermove", function (e) { if (e.buttons || e.pointerType === "mouse") inspect(e); });
    cv.addEventListener("pointerleave", function () { q("#" + id + "-px", host).hidden = true; });
    draw();
    return {
      set: function (np) {
        Object.assign(p, np);
        setSeg(segs[0], p.view); setSeg(segs[1], p.water);
        q("#" + id + "-d", host).value = p.dist; q("#" + id + "-l", host).value = p.light; q("#" + id + "-t", host).value = p.thr;
        q("#" + id + "-px", host).hidden = true; draw();
      }
    };
  }

  /* ---------------- instrument: filter lab ---------------- */
  function mountFilter(host) {
    var id = "fl" + (++uid), S = scene(), W = S.W, H = S.H, N = S.N, I = new Float32Array(N * 3);
    renderScene(S, { dist: 2.5, water: "coastal", light: 0.35 }, I);
    var gray = new Float32Array(N); for (var i = 0; i < N; i++) gray[i] = 0.299 * I[3 * i] + 0.587 * I[3 * i + 1] + 0.114 * I[3 * i + 2];
    var K = { orig: [[0, 0, 0], [0, 1, 0], [0, 0, 0]], blur: [[1, 1, 1], [1, 1, 1], [1, 1, 1]].map(function (r) { return r.map(function (v) { return v / 9; }); }),
      sharp: [[0, -1, 0], [-1, 5, -1], [0, -1, 0]], edge: [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]] };
    var TXT = { orig: "The picture as the computer receives it: one brightness number per pixel. Dusk light makes it grainy.",
      blur: "Each pixel becomes the average of its 3 × 3 neighbourhood. Noise drops; fins and edges soften.",
      sharp: "Each pixel is pushed away from its neighbours’ average. Edges pop, and so does noise.",
      edge: "Sobel kernels compare one side of each pixel with the other. Bright lines mark edges. Turn on “Blur first” to stop noise becoming edges.",
      thr: "Every pixel brighter than the background by more than the threshold becomes white. Otsu’s method picks the threshold automatically from the histogram." };
    var p = { k: "orig", pre: false };
    var view = '<div class="lc-dual"><figure><canvas width="360" height="216" id="' + id + '-a"></canvas><figcaption>Input</figcaption></figure><figure><canvas width="360" height="216" id="' + id + '-b"></canvas><figcaption id="' + id + '-cap">Output</figcaption></figure></div>';
    var ctrl = '<span class="lc-ctl-label">Kernel</span>' + seg("Kernel", [["orig", "None"], ["blur", "Blur"], ["sharp", "Sharpen"], ["edge", "Edges"], ["thr", "Threshold"]], "orig") +
      '<div style="height:.9rem"></div><label class="lc-check"><input type="checkbox" id="' + id + '-pre"> Blur first</label><div style="height:.9rem"></div><span class="lc-ctl-label">The 3 × 3 weights</span><div class="lc-kernel" id="' + id + '-k"></div>';
    host.innerHTML = inst("Filter lab", "the kernels from Module 03", view, ctrl, true);
    function conv(src, k) {
      var out = new Float32Array(N);
      for (var y = 0; y < H; y++) for (var x = 0; x < W; x++) {
        var s = 0; for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) { var yy = Math.min(H - 1, Math.max(0, y + dy)), xx = Math.min(W - 1, Math.max(0, x + dx)); s += k[dy + 1][dx + 1] * src[yy * W + xx]; }
        out[y * W + x] = s;
      } return out;
    }
    function otsu(v) {
      var hist = new Float64Array(256), lo = Infinity, hi = -Infinity, i;
      for (i = 0; i < v.length; i++) { if (v[i] < lo) lo = v[i]; if (v[i] > hi) hi = v[i]; }
      for (i = 0; i < v.length; i++) hist[Math.min(255, Math.floor((v[i] - lo) / (hi - lo + 1e-9) * 256))]++;
      var tot = v.length, sum = 0, sumB = 0, wB = 0, best = 0, bi = 0;
      for (i = 0; i < 256; i++) sum += i * hist[i];
      for (i = 0; i < 256; i++) { wB += hist[i]; if (!wB) continue; var wF = tot - wB; if (!wF) break; sumB += i * hist[i]; var mB = sumB / wB, mF = (sum - sumB) / wF, b = wB * wF * (mB - mF) * (mB - mF); if (b > best) { best = b; bi = i; } }
      return lo + (bi + 0.5) / 256 * (hi - lo);
    }
    function paint(cv, arr, scale, off) {
      var g = cv.getContext("2d"), im = g.createImageData(W, H);
      for (var i = 0; i < N; i++) { var v = Math.max(0, Math.min(255, 255 * (arr[i] * scale + off))); im.data[4 * i] = v * 0.92; im.data[4 * i + 1] = v; im.data[4 * i + 2] = v; im.data[4 * i + 3] = 255; }
      g.putImageData(im, 0, 0);
    }
    function draw() {
      var src = p.pre ? conv(gray, K.blur) : gray, out, scale = 1, off = 0, k = K[p.k] || K.orig, cap = "Output";
      if (p.k === "edge") { var gx = conv(src, K.edge), gy = conv(src, [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]); out = new Float32Array(N); for (var i = 0; i < N; i++) out[i] = Math.hypot(gx[i], gy[i]); scale = 2.2; cap = "Edge strength"; }
      else if (p.k === "thr") { var bgv = src[5 * W + 5], d = new Float32Array(N); for (var j = 0; j < N; j++) d[j] = Math.abs(src[j] - bgv); var t = otsu(d); out = new Float32Array(N); for (var m = 0; m < N; m++) out[m] = d[m] > t ? 1 : 0; cap = "Mask, Otsu threshold " + t.toFixed(3); k = null; }
      else { out = conv(src, k); cap = p.k === "orig" ? "Output (no kernel)" : "Output"; }
      paint(q("#" + id + "-a", host), gray, 1, 0); paint(q("#" + id + "-b", host), out, scale, off);
      q("#" + id + "-cap", host).textContent = cap;
      q("#" + id + "-k", host).innerHTML = k ? (p.k === "edge" ? K.edge : k).map(function (r) { return r.map(function (v) { return "<span>" + (Math.abs(v - Math.round(v)) > 1e-6 ? "1/9" : v) + "</span>"; }).join(""); }).join("") : "<span>—</span><span>—</span><span>—</span>";
      q(".finding", host).innerHTML = "<b>" + { orig: "No filter.", blur: "Blur.", sharp: "Sharpen.", edge: "Edges.", thr: "Threshold." }[p.k] + "</b> " + TXT[p.k];
    }
    bindSeg(q(".seg", host), function (v) { p.k = v; draw(); });
    q("#" + id + "-pre", host).addEventListener("change", function (e) { p.pre = e.target.checked; draw(); });
    draw();
  }

  /* ---------------- instrument: abstention ---------------- */
  function mountAbstain(host) {
    var id = "ab" + (++uid), r = rng(11), n = 600, conf = [], ok = [];
    for (var i = 0; i < n; i++) { var c = Math.max(0.34, 1 - 0.66 * Math.pow(r(), 1.8)), pc = 0.25 + 0.74 * Math.pow((c - 0.34) / 0.66, 0.7); conf.push(c); ok.push(r() < pc); }
    function stats(th) { var k = 0, gd = 0; for (var i = 0; i < n; i++) if (conf[i] >= th) { k++; if (ok[i]) gd++; } return { cov: k / n, acc: k ? gd / k : NaN, rev: n - k }; }
    var grid = []; for (var t = 0.34; t <= 0.991; t += 0.01) grid.push([t, stats(t)]);
    var view = '<canvas width="560" height="240" id="' + id + '-cv" role="img" aria-label="Coverage and accuracy against the confidence threshold"></canvas><div class="legend"><span><i style="background:' + CK.ice + '"></i>frames the model decides</span><span><i style="background:' + CK.good + '"></i>accuracy on those frames</span><span><i style="background:' + CK.glow + '"></i>your threshold</span></div>' +
      '<div class="readouts"><div class="ro"><b id="' + id + '-c"></b><span>frames decided</span></div><div class="ro good"><b id="' + id + '-a"></b><span>right, of those</span></div><div class="ro hot"><b id="' + id + '-r"></b><span>of 600 sent to a person</span></div></div>';
    host.innerHTML = inst("Saying “I don’t know”", "600 test frames from Module 04", view, range(id + "-t", "Confidence needed to decide", 0.34, 0.99, 0.01, 0.7) + '<p class="small" style="color:var(--deep-muted)">Below the threshold the model answers “unknown” and the frame goes to a person.</p>', true);
    function draw() {
      var th = +q("#" + id + "-t", host).value, s = stats(th), d = hidpi(q("#" + id + "-cv", host), true), g = d.g, w = d.w, h = d.h, L = 40, R = w - 12, T = 12, B = h - 28;
      var X = function (v) { return L + (v - 0.34) / 0.65 * (R - L); }, Y = function (v) { return B - v * (B - T); };
      g.clearRect(0, 0, w, h); g.strokeStyle = CK.line; g.fillStyle = CK.muted; g.lineWidth = 1;
      [0, 0.5, 1].forEach(function (v) { g.beginPath(); g.moveTo(L, Y(v)); g.lineTo(R, Y(v)); g.stroke(); g.fillText(Math.round(100 * v) + "%", 4, Y(v) + 4); });
      [0.4, 0.6, 0.8, 0.95].forEach(function (v) { g.fillText(v.toFixed(2), X(v) - 12, h - 8); });
      [["cov", CK.ice], ["acc", CK.good]].forEach(function (s2) { g.strokeStyle = s2[1]; g.lineWidth = 2.5; g.beginPath(); grid.forEach(function (gp, k) { var y = Y(gp[1][s2[0]]); k ? g.lineTo(X(gp[0]), y) : g.moveTo(X(gp[0]), y); }); g.stroke(); });
      g.strokeStyle = CK.glow; g.lineWidth = 3; g.beginPath(); g.moveTo(X(th), T); g.lineTo(X(th), B); g.stroke();
      q("#" + id + "-t-o", host).textContent = th.toFixed(2);
      q("#" + id + "-c", host).textContent = pct(s.cov); q("#" + id + "-a", host).textContent = pct(s.acc); q("#" + id + "-r", host).textContent = s.rev;
      q(".finding", host).innerHTML = "<b>At " + th.toFixed(2) + ",</b> the model decides " + pct(s.cov) + " of frames and is right on " + pct(s.acc) + " of them. " + s.rev + " frames wait for a person. Neither extreme is right for every use: a ship-strike alert and a fish census want different settings.";
    }
    q("#" + id + "-t", host).addEventListener("input", draw); draw();
    return draw;
  }

  /* ---------------- instrument: flat port ---------------- */
  function mountPort(host) {
    var id = "fp" + (++uid), n = 1.33, Z = 1, L = 0.30;
    var view = '<svg viewBox="0 0 560 220" role="img" aria-label="Diagram of a ray bending at a flat camera window" style="width:100%;height:auto;display:block;background:' + CK.bg + ';border-radius:8px"><rect x="0" y="0" width="300" height="220" fill="#0B3340"/><text x="14" y="22" fill="' + CK.muted + '" font-size="13">water</text><text x="320" y="22" fill="' + CK.muted + '" font-size="13">air, inside the housing</text><line x1="300" y1="0" x2="300" y2="220" stroke="' + CK.ice + '" stroke-width="3"/><circle cx="470" cy="110" r="9" fill="' + CK.ink + '"/><text x="440" y="140" fill="' + CK.muted + '" font-size="13">camera</text><line x1="40" y1="110" x2="470" y2="110" stroke="' + CK.line + '" stroke-dasharray="4 4"/><path id="' + id + '-ray" fill="none" stroke="' + CK.glow + '" stroke-width="3"/><path id="' + id + '-air" fill="none" stroke="' + CK.muted + '" stroke-width="1.5" stroke-dasharray="5 5"/></svg>' +
      '<div class="readouts"><div class="ro bad"><b id="' + id + '-a"></b><span>length error, calibrated in air</span></div><div class="ro"><b id="' + id + '-m"></b><span>weight error that follows</span></div><div class="ro good"><b id="' + id + '-f"></b><span>length error after ÷ 1.33</span></div></div>';
    host.innerHTML = inst("Flat camera window", "a 30 cm fish, 1 m away", view, range(id + "-ang", "Fish position off the camera axis", 0, 40, 1, 10) + '<p class="small" style="color:var(--deep-muted)">The yellow ray bends where it crosses the window. The dashed line is where an in-air calibration assumes it came from. No ray beyond about 48.8° in water reaches the camera at all.</p>', true);
    function xs(X) { return Math.tan(Math.asin(Math.min(1, n * Math.sin(Math.atan2(X, Z))))); }
    function sg(v) { return (v >= 0 ? "+" : "−") + Math.abs(Math.round(100 * v)) + "%"; }
    function draw() {
      var deg = +q("#" + id + "-ang", host).value, th = deg * Math.PI / 180, X0 = Z * Math.tan(th);
      var est = (xs(X0 + L / 2) - xs(X0 - L / 2)) * Z, eA = est / L - 1, eF = est / n / L - 1, mass = Math.pow(1 + eA, 3) - 1;
      var thA = Math.asin(Math.min(1, n * Math.sin(th))), cy = 110, px = 300;
      var yPort = cy - (470 - px) * Math.tan(thA), yFish = yPort - (px - 40) * Math.tan(th), yAir = yPort - (px - 40) * Math.tan(thA);
      q("#" + id + "-ray", host).setAttribute("d", "M40 " + yFish.toFixed(1) + " L" + px + " " + yPort.toFixed(1) + " L470 " + cy);
      q("#" + id + "-air", host).setAttribute("d", "M40 " + yAir.toFixed(1) + " L" + px + " " + yPort.toFixed(1));
      q("#" + id + "-ang-o", host).textContent = deg + "°";
      q("#" + id + "-a", host).textContent = sg(eA); q("#" + id + "-m", host).textContent = sg(mass); q("#" + id + "-f", host).textContent = sg(eF);
      q(".finding", host).innerHTML = "<b>" + (deg < 8 ? "Near the centre" : deg < 25 ? "Partway out" : "Near the edge") + ",</b> an in-air calibration makes this fish " + sg(eA) + " long, so its estimated weight is " + sg(mass) + " heavy. Dividing by 1.33 fixes the centre of the frame, not the edges. Calibrate underwater, at working distance.";
    }
    q("#" + id + "-ang", host).addEventListener("input", draw); draw();
  }

  /* ---------------- instrument: Kalman ---------------- */
  function mountKalman(host) {
    var id = "kf" + (++uid), Tn = 150, r = rng(5), gx = [], gy = [], u = [], tx = [], ty = [];
    for (var t = 0; t < Tn; t++) { gx.push(gauss(r)); gy.push(gauss(r)); u.push(r()); tx.push(30 + 3.3 * t); ty.push(118 + 58 * Math.sin(t / 16) + 15 * Math.sin(t / 5.5)); }
    var inPatch = function (x) { return x >= 230 && x <= 330; };
    var view = '<canvas width="560" height="230" id="' + id + '-cv" role="img" aria-label="A fish’s true path, its noisy detections, and the Kalman estimate"></canvas><div class="legend"><span><i style="background:' + CK.muted + '"></i>true path</span><span><i style="background:' + CK.ink + '"></i>detections</span><span><i style="background:' + CK.glow + '"></i>Kalman estimate</span></div>' +
      '<div class="readouts"><div class="ro"><b id="' + id + '-raw"></b><span>raw detection error</span></div><div class="ro good"><b id="' + id + '-k"></b><span>Kalman error, same frames</span></div><div class="ro hot"><b id="' + id + '-c"></b><span>Kalman error while coasting</span></div></div>';
    var ctrl = range(id + "-r", "Detection noise", 1, 15, 0.5, 6) + range(id + "-q", "How sharply the fish may turn", -2, 1, 0.05, -0.5) + '<label class="lc-check"><input type="checkbox" id="' + id + '-p" checked> Murky patch (most detections lost)</label>';
    host.innerHTML = inst("Tracking one fish", "a constant-velocity Kalman filter", view, ctrl, true);
    function draw() {
      var sd = +q("#" + id + "-r", host).value, qq = Math.pow(10, +q("#" + id + "-q", host).value), patch = q("#" + id + "-p", host).checked;
      var mx = [], my = [], has = [], t;
      for (t = 0; t < Tn; t++) { mx.push(tx[t] + sd * gx[t]); my.push(ty[t] + sd * gy[t]); has.push(!(patch && inPatch(tx[t]) ? u[t] < 0.85 : u[t] < 0.08)); }
      var t0 = has.indexOf(true), R = sd * sd, s = [mx[t0], my[t0], 0, 0], P = [[R, 0, 0, 0], [0, R, 0, 0], [0, 0, 25, 0], [0, 0, 0, 25]], ex = [], ey = [];
      function mm(A, B) { return A.map(function (row) { return B[0].map(function (_, j) { return row.reduce(function (a, v, k) { return a + v * B[k][j]; }, 0); }); }); }
      function tr(A) { return A[0].map(function (_, j) { return A.map(function (row) { return row[j]; }); }); }
      var F = [[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], G = [[0.5, 0], [0, 0.5], [1, 0], [0, 1]], Q = mm(G, tr(G)).map(function (row) { return row.map(function (v) { return qq * v; }); });
      for (t = 0; t < Tn; t++) {
        if (t > t0) {
          s = [s[0] + s[2], s[1] + s[3], s[2], s[3]];
          P = mm(mm(F, P), tr(F)).map(function (row, i) { return row.map(function (v, j) { return v + Q[i][j]; }); });
          if (has[t]) {
            var S = [[P[0][0] + R, P[0][1]], [P[1][0], P[1][1] + R]], det = S[0][0] * S[1][1] - S[0][1] * S[1][0], Si = [[S[1][1] / det, -S[0][1] / det], [-S[1][0] / det, S[0][0] / det]];
            var K = P.map(function (row) { return [row[0] * Si[0][0] + row[1] * Si[1][0], row[0] * Si[0][1] + row[1] * Si[1][1]]; }), y0 = mx[t] - s[0], y1 = my[t] - s[1];
            s = s.map(function (v, i) { return v + K[i][0] * y0 + K[i][1] * y1; });
            P = mm(K.map(function (k, i) { return [k[0], k[1], 0, 0].map(function (v, j) { return (i === j ? 1 : 0) - v; }); }), P);
          }
        }
        ex.push(s[0]); ey.push(s[1]);
      }
      var eR = 0, eK = 0, nS = 0, eG = 0, nG = 0;
      for (t = t0; t < Tn; t++) { var dk = Math.hypot(ex[t] - tx[t], ey[t] - ty[t]); if (has[t]) { eR += Math.hypot(mx[t] - tx[t], my[t] - ty[t]); eK += dk; nS++; } else if (patch && inPatch(tx[t])) { eG += dk; nG++; } }
      var d = hidpi(q("#" + id + "-cv", host), false), g = d.g, w = d.w, h = d.h;
      g.fillStyle = CK.bg; g.fillRect(0, 0, w, h);
      if (patch) { g.fillStyle = "rgba(158,216,230,.10)"; g.fillRect(230, 0, 100, h); g.fillStyle = CK.muted; g.fillText("murky patch", 248, h - 10); }
      g.setLineDash([5, 4]); g.strokeStyle = CK.muted; g.lineWidth = 1.5; g.beginPath(); for (t = 0; t < Tn; t++) t ? g.lineTo(tx[t], ty[t]) : g.moveTo(tx[t], ty[t]); g.stroke(); g.setLineDash([]);
      g.fillStyle = CK.ink; for (t = 0; t < Tn; t++) if (has[t]) { g.beginPath(); g.arc(mx[t], my[t], 2.2, 0, 7); g.fill(); }
      g.strokeStyle = CK.glow; g.lineWidth = 2.5; g.beginPath(); for (t = t0; t < Tn; t++) t > t0 ? g.lineTo(ex[t], ey[t]) : g.moveTo(ex[t], ey[t]); g.stroke();
      q("#" + id + "-r-o", host).textContent = sd.toFixed(1) + " px";
      q("#" + id + "-q-o", host).textContent = qq < 0.1 ? "rarely" : qq < 1 ? "sometimes" : "often";
      q("#" + id + "-raw", host).textContent = (eR / nS).toFixed(1) + " px"; q("#" + id + "-k", host).textContent = (eK / nS).toFixed(1) + " px"; q("#" + id + "-c", host).textContent = nG ? (eG / nG).toFixed(1) + " px" : "n/a";
      q(".finding", host).innerHTML = "<b>Where detections exist,</b> the filter’s estimate is " + (eK < eR ? "closer to the truth than the raw detections" : "no better than the raw detections at this setting") + ". " + (nG ? "In the murky patch it coasts on its prediction, and its error grows until the fish reappears." : "Turn the murky patch on to see it coast.") + " Raise “how sharply the fish may turn” and it follows wiggles but smooths less.";
    }
    ["-r", "-q", "-p"].forEach(function (s) { q("#" + id + s, host).addEventListener("input", draw); });
    draw();
    return draw;
  }

  /* ---------------- instrument: occupancy ---------------- */
  function mountOcc(host) {
    var id = "oc" + (++uid), r = rng(3), weather = [];
    for (var i = 0; i < 500; i++) weather.push(0.9 * (-Math.log(r()) - Math.log(r())));
    var NEAR = 0.532, FAR = 0.0305, p = { plume: 3, K: 6, psiOut: 0.6 };
    function group(near) {
      var ep = 0; weather.forEach(function (w) { ep += expit(2 - 0.7 * (1 + p.plume * near + w)); }); ep /= weather.length;
      var psi = 0.6 + (p.psiOut - 0.6) * near; return { psi: psi, visit: psi * ep, ever: psi * (1 - Math.pow(1 - ep, p.K)) };
    }
    var view = '<canvas width="560" height="250" id="' + id + '-cv" role="img" aria-label="Bar chart comparing sites near and far from the outfall"></canvas><div class="legend"><span><i style="background:' + CK.warn + '"></i>sites 0–1 km from the outfall</span><span><i style="background:' + CK.ice + '"></i>sites 2–3 km away</span></div>' +
      '<div class="readouts"><div class="ro bad"><b id="' + id + '-v"></b><span>fewer detections near the outfall</span></div><div class="ro"><b id="' + id + '-t"></b><span>real difference in fish</span></div></div>';
    var ctrl = range(id + "-p", "Extra murk near the outfall", 0, 5, 0.1, 3) + range(id + "-k", "Visits per site", 1, 10, 1, 6) + '<span class="lc-ctl-label">The real world</span>' + seg("The real world", [["0.6", "No impact"], ["0.25", "Fewer fish near the outfall"]], "0.6") + '<p class="small" style="color:var(--deep-muted);margin-top:.8rem">Long-run averages from Module 09’s model. Any single survey adds noise.</p>';
    host.innerHTML = inst("Seen versus there", "the occupancy model from Module 09", view, ctrl, true);
    function draw() {
      p.plume = +q("#" + id + "-p", host).value; p.K = +q("#" + id + "-k", host).value;
      var nr = group(NEAR), fr = group(FAR), cats = [["Visits with", "a detection", "visit"], ["Sites ever", "detected", "ever"], ["Occupancy-model", "estimate", "psi"], ["True", "occupancy", "psi"]];
      var d = hidpi(q("#" + id + "-cv", host), true), g = d.g, w = d.w, h = d.h, L = 36, B = h - 40, T = 14, gw = (w - L - 8) / 4, bw = gw * 0.3, Y = function (v) { return B - v / 0.8 * (B - T); };
      g.clearRect(0, 0, w, h); g.strokeStyle = CK.line; g.fillStyle = CK.muted;
      [0, 0.2, 0.4, 0.6].forEach(function (v) { g.beginPath(); g.moveTo(L, Y(v)); g.lineTo(w - 8, Y(v)); g.stroke(); g.fillText(v.toFixed(1), 4, Y(v) + 4); });
      cats.forEach(function (c, k) {
        var x0 = L + k * gw + gw * 0.18;
        [[nr, CK.warn], [fr, CK.ice]].forEach(function (pair, j) { var v = pair[0][c[2]]; g.globalAlpha = k === 3 ? 0.5 : 1; g.fillStyle = pair[1]; g.fillRect(x0 + j * (bw + 3), Y(v), bw, B - Y(v)); g.globalAlpha = 1; g.fillStyle = CK.ink; g.textAlign = "center"; g.fillText(v.toFixed(2), x0 + j * (bw + 3) + bw / 2, Y(v) - 4); });
        g.fillStyle = CK.muted; g.textAlign = "center"; g.fillText(c[0], x0 + bw + 1.5, B + 15); g.fillText(c[1], x0 + bw + 1.5, B + 29); g.textAlign = "left";
      });
      var drop = 1 - nr.visit / fr.visit, truth = 1 - nr.psi / fr.psi;
      q("#" + id + "-p-o", host).textContent = p.plume.toFixed(1); q("#" + id + "-k-o", host).textContent = p.K;
      q("#" + id + "-v", host).textContent = pct(drop); q("#" + id + "-t", host).textContent = truth < 0.005 ? "none" : pct(truth);
      q(".finding", host).innerHTML = truth < 0.005 ? "<b>No real impact,</b> yet visits near the outfall record a detection " + pct(drop) + " less often, because the water there is murkier. An occupancy model, using repeat visits, recovers the true value on average." : "<b>A real impact:</b> " + pct(truth) + " fewer fish near the outfall. The raw detection gap (" + pct(drop) + ") exaggerates it, because murk and real loss add up. Only a model that separates them tells you how much is real.";
    }
    ["-p", "-k"].forEach(function (s) { q("#" + id + s, host).addEventListener("input", draw); });
    bindSeg(q(".seg", host), function (v) { p.psiOut = +v; draw(); });
    draw();
    return draw;
  }

  /* ---------------- static figures ---------------- */
  function figConditions(host) {
    var rows = [["Clean frames", 0.93], ["Turbid (artificial haze)", 0.80], ["Low light", 0.60], ["Blur", 0.60], ["Turbid and blur", 0.45], ["Fish farther away (physics)", 0.55], ["Trained on reef, tested in harbour", 0.71]];
    host.innerHTML = '<figure class="lc-figure"><div class="lc-hbar">' + rows.map(function (r) { return "<span>" + r[0] + '</span><span class="t"><i class="' + (r[1] < 0.75 ? "low" : "") + '" style="width:' + (100 * r[1]) + '%"></i></span><span class="v">' + r[1].toFixed(2) + "</span>"; }).join("") + "</div><figcaption>Accuracy of the same model under different conditions, from a test run of the Module 05 notebook. One overall number would have hidden every orange bar.</figcaption></figure>";
  }
  function figCnn(host) {
    var rows = [["Linear model", "0.63", "0.76", "0.64", "0.63", "0.51"], ["Fully connected network", "0.60", "0.54", "0.61", "0.60", "0.43"], ["Small CNN", "0.78", "0.76", "0.38", "0.69", "0.34"], ["Small CNN, each frame standardised", "0.93", "0.93", "0.96", "0.51", "0.72"], ["…plus augmentation", "0.99", "0.99", "0.99", "0.94", "0.68"]];
    host.innerHTML = '<div class="scroll"><table><thead><tr><th>Model</th><th>Clean</th><th>Haze</th><th>Low light</th><th>Blur</th><th>Farther (physics)</th></tr></thead><tbody>' + rows.map(function (r) { return "<tr><td>" + r[0] + "</td><td>" + r.slice(1).join("</td><td>") + "</td></tr>"; }).join("") + '</tbody></table></div><p class="small muted" style="margin-top:.6rem">Accuracy from a test run of the Module 06 notebook. Look down the last column: near-perfect scores under artificial haze, but not on fish that are really farther away.</p>';
  }

  /* ---------------- module reader ---------------- */
  function nbButtons(file) {
    var base = root.dataset.colabBase || "", gh = root.dataset.githubBase || "";
    return (base ? '<a class="btn glow" href="' + base + file + '" target="_blank" rel="noopener">Open in Colab</a>' : "") + (gh ? '<a class="btn line" href="' + gh + file + '" target="_blank" rel="noopener">View on GitHub</a>' : "");
  }
  function renderModule(m) {
    var i = m.n - 1, prev = MODULES[i - 1], next = MODULES[i + 1], path = PATHS.filter(function (p) { return p.id === state.path; })[0];
    var onPath = path && path.id !== "all" && path.mods.indexOf(m.n) >= 0;
    var h = '<a class="lc-back" href="#/learn/course">Back to all modules</a>';
    h += '<header class="lc-mhead"><p class="num">Module ' + pad(m.n) + ", " + m.depth + ' m down</p><h1>' + m.title + '</h1><p class="why">' + m.why + '</p><div class="facts"><span class="lc-tag">' + m.time + '</span><span class="lc-tag">Notebook: ' + m.nb.run + " to run</span>" + (onPath ? '<span class="lc-tag read">On your path: ' + esc(path.label) + "</span>" : "") + (state.done[m.n] ? '<span class="lc-tag" style="color:var(--ok)">Completed</span>' : "") + '<button type="button" class="btn line sm lc-copy" id="lc-copy">Copy link to this module</button></div></header>';
    h += "<section><h2>You’ll be able to</h2><ul class=\"lc-goals\">" + m.goals.map(function (g) { return "<li>" + g + "</li>"; }).join("") + "</ul></section>";
    h += '<section><h2>The lesson</h2><div class="lc-prose">' + m.lesson.map(function (l) { return l.indexOf('<span class="lc-eq">') === 0 ? l.replace('<span class="lc-eq">', '<div class="lc-eq">').replace(/<\/span>$/, "</div>") : "<p>" + l + "</p>"; }).join("") + "</div></section>";
    h += '<section><h2>Try it</h2><div id="lc-demo"></div></section>';
    if (m.project) h += '<section><div class="lc-box lc-proj"><h3>From the project</h3><p style="margin:0">' + m.project.replace(/^(From the project|For Capstone B): /, "") + "</p></div></section>";
    h += '<section class="lc-twocol"><div class="lc-box lc-warn"><h3>Common mistakes</h3><ul>' + m.mistakes.map(function (x) { return "<li>" + x + "</li>"; }).join("") + '</ul></div><div class="lc-box lc-fx"><h3>In the field: ' + m.field.t + '</h3><p style="margin:0 0 .5rem">' + m.field.b + "</p>" + (m.field.url ? '<a href="' + m.field.url + '" target="_blank" rel="noopener">Read the source</a>' : "") + "</div></section>";
    if (m.extra) h += '<section class="lc-box" style="max-width:var(--measure)">' + m.extra + "</section>";
    h += '<section><h2>The notebook</h2><div class="lc-nbcard"><div><h3><code>' + m.nb.file + "</code></h3><p>" + m.nb.inside + '</p><p class="small">Runs top to bottom on Colab’s free CPU in ' + m.nb.run + ". Choose File, Save a copy in Drive first.</p></div><div class=\"row\">" + nbButtons(m.nb.file) + "</div></div></section>";
    h += '<section><h2>Check yourself</h2><div class="lc-quiz">' + m.quiz.map(function (qq, k) {
      return '<div class="lc-q" data-q="' + k + '"><p>' + (k + 1) + ". " + qq[0] + '</p><div class="lc-opts">' + qq[1].map(function (o, j) { return '<button type="button" class="lc-opt" data-j="' + j + '" aria-pressed="false">' + esc(o) + "</button>"; }).join("") + '</div><p class="lc-fb" aria-live="polite"></p></div>';
    }).join("") + '</div><p class="lc-score" id="lc-score" aria-live="polite"></p></section>';
    h += '<section><h2>Go further</h2><ul class="lc-further">' + m.further.map(function (f) { return '<li><a href="' + f[2] + '" target="_blank" rel="noopener">' + f[0] + "</a><span>" + f[1] + "</span></li>"; }).join("") + "</ul></section>";
    h += '<div class="lc-complete"><button type="button" class="btn acc" id="lc-done" aria-pressed="' + !!state.done[m.n] + '">' + (state.done[m.n] ? "Completed. Mark as not done" : "Mark this module complete") + '</button><span class="small muted">Saved on this device only.</span></div>';
    h += '<nav class="lc-pager" aria-label="Previous and next module">' + (prev ? '<a href="#/learn/m' + pad(prev.n) + '"><small>Previous</small><b>' + pad(prev.n) + " " + prev.title + "</b></a>" : "<span></span>") + (next ? '<a class="nx" href="#/learn/m' + pad(next.n) + '"><small>Next</small><b>' + pad(next.n) + " " + next.title + '</b></a>' : '<a class="nx" href="#/learn/course"><small>Finished the modules?</small><b>Choose a capstone</b></a>') + "</nav>";
    var art = q("#lc-article"); art.innerHTML = h;
    var demo = q("#lc-demo"), D = m.demo.type;
    if (D === "camera") mountCamera(demo, m.demo.preset); else if (D === "filter") mountFilter(demo); else if (D === "abstain") mountAbstain(demo);
    else if (D === "port") mountPort(demo); else if (D === "kalman") mountKalman(demo); else if (D === "occ") mountOcc(demo);
    else if (D === "conditions") figConditions(demo); else if (D === "cnn") figCnn(demo);
    var answers = state.quiz[m.n] || {};
    qa(".lc-q", art).forEach(function (box) {
      var k = +box.dataset.q, item = m.quiz[k];
      function pick(j, silent) {
        qa(".lc-opt", box).forEach(function (b) { var on = +b.dataset.j === j; b.setAttribute("aria-pressed", on); b.classList.toggle("right", on && j === item[2]); b.classList.toggle("wrong", on && j !== item[2]); });
        var fb = q(".lc-fb", box); fb.className = "lc-fb " + (j === item[2] ? "right" : "wrong");
        fb.innerHTML = (j === item[2] ? "<b>Right.</b> " : "<b>Not quite.</b> ") + item[3];
        answers[k] = j; state.quiz[m.n] = answers; if (!silent) save("quiz", state.quiz); score();
      }
      qa(".lc-opt", box).forEach(function (b) { b.addEventListener("click", function () { pick(+b.dataset.j); }); });
      if (answers[k] !== undefined) pick(answers[k], true);
    });
    function score() { var got = 0, n = 0; m.quiz.forEach(function (it, k) { if (answers[k] !== undefined) { n++; if (answers[k] === it[2]) got++; } }); q("#lc-score").textContent = n ? got + " of " + m.quiz.length + " right" + (n < m.quiz.length ? " so far" : got === m.quiz.length ? ". Well done." : ". Try the others again.") : ""; }
    score();
    q("#lc-copy").addEventListener("click", function () { var url = location.href.split("#")[0] + "#/learn/m" + pad(m.n); if (window.AGU && window.AGU.copy) window.AGU.copy(url, "Link"); else if (navigator.clipboard) navigator.clipboard.writeText(url); });
    q("#lc-done").addEventListener("click", function () { if (state.done[m.n]) delete state.done[m.n]; else state.done[m.n] = true; save("done", state.done); renderModule(m); renderIndex(m.n); renderMap(); });
    renderIndex(m.n);
  }
  function renderIndex(active) {
    q("#lc-index").innerHTML = '<p class="small muted" style="margin:0 0 .5rem">Modules</p>' + MODULES.map(function (m) {
      return '<a href="#/learn/m' + pad(m.n) + '"' + (m.n === active ? ' aria-current="page"' : "") + '><span class="k">' + pad(m.n) + "</span><span>" + m.title + "</span>" + (state.done[m.n] ? '<span class="ok" aria-label="completed">✓</span>' : "") + "</a>";
    }).join("") + '<p style="margin-top:1rem"><a class="lc-back" href="#/learn/teach" style="padding:0;border:0">Teach with this</a></p>';
  }

  /* ---------------- overview: paths, map, glossary, tour, art ---------------- */
  function renderMap() {
    var path = PATHS.filter(function (p) { return p.id === state.path; })[0] || PATHS[0];
    q("#lc-map").innerHTML = MODULES.map(function (m) {
      var on = path.mods.indexOf(m.n) >= 0, col = css(seen(ORANGE, m.depth, "coastal"));
      return '<li><a class="lc-card' + (on ? "" : " lc-off") + '" href="#/learn/m' + pad(m.n) + '" style="--depth:' + col + '">' + (state.done[m.n] ? '<span class="done">✓ Done</span>' : "") +
        '<span class="n"><b>' + pad(m.n) + "</b><span>" + m.depth + " m down</span></span><h3>" + m.title + "</h3><p>" + m.one + '</p><span class="foot"><span class="lc-tag">' + m.time + "</span>" + (path.read && on ? '<span class="lc-tag read">Read the page</span>' : "") + (path.id !== "all" && !on ? "<span>Optional for your path</span>" : "") + "</span></a></li>";
    }).join("");
    q("#lc-path-text").textContent = path.text;
    var n = Object.keys(state.done).length;
    q("#lc-prog-text").textContent = n + " of 9 done"; q("#lc-prog-bar").style.width = (100 * n / 9) + "%";
  }
  function bindPaths() {
    var box = q("#lc-paths");
    box.innerHTML = PATHS.map(function (p) { return '<button type="button" data-p="' + p.id + '" aria-pressed="' + (p.id === state.path) + '">' + p.label + "<small>" + p.sub + "</small></button>"; }).join("");
    qa("button", box).forEach(function (b) { b.addEventListener("click", function () { state.path = b.dataset.p; save("path", state.path); qa("button", box).forEach(function (x) { x.setAttribute("aria-pressed", x === b); }); renderMap(); }); });
  }
  function bindGlossary() {
    var dl = q("#lc-gloss");
    dl.innerHTML = GLOSSARY.map(function (g) { return '<div data-t="' + esc((g[0] + " " + g[1]).toLowerCase()) + '"><dt>' + g[0] + "</dt><dd>" + g[1] + ' <a href="#/learn/m' + pad(g[2]) + '">Module ' + pad(g[2]) + "</a></dd></div>"; }).join("");
    q("#lc-gfilter").addEventListener("input", function (e) { var v = e.target.value.trim().toLowerCase(); qa("div", dl).forEach(function (d) { d.hidden = v && d.dataset.t.indexOf(v) < 0; }); });
  }
  function bindTour() {
    var cam = mountCamera(q("#lc-cam-tour"), TOUR[0].preset), step = 0, nav = q("#lc-steps");
    nav.innerHTML = TOUR.map(function (t, i) { return '<button type="button" data-s="' + i + '" aria-pressed="' + (i === 0) + '">' + (i + 1) + "</button>"; }).join("");
    function go(i) {
      step = Math.max(0, Math.min(TOUR.length - 1, i));
      q("#lc-step-text").innerHTML = '<p class="lc-step-count">Step ' + (step + 1) + " of " + TOUR.length + "</p><h3>" + TOUR[step].title + "</h3>" + TOUR[step].body;
      qa("button", nav).forEach(function (b) { b.setAttribute("aria-pressed", +b.dataset.s === step); b.setAttribute("aria-label", "Step " + (+b.dataset.s + 1) + ": " + TOUR[+b.dataset.s].title); });
      q("#lc-prev").disabled = step === 0;
      q("#lc-next").textContent = step === TOUR.length - 1 ? "Start the course" : "Next step";
      cam.set(TOUR[step].preset);
    }
    qa("button", nav).forEach(function (b) { b.addEventListener("click", function () { go(+b.dataset.s); }); });
    q("#lc-prev").addEventListener("click", function () { go(step - 1); });
    q("#lc-next").addEventListener("click", function () { if (step === TOUR.length - 1) location.hash = "#/learn/course"; else go(step + 1); });
    go(0);
    return cam;
  }
  function drawArt() {
    var gEl = document.getElementById("lc-art-fish"); if (!gEl) return;
    var fish = [[120, 90, 1, 0], [250, 150, 3, 1], [390, 110, 6, 1], [180, 250, 10, 0], [330, 290, 18, 1], [470, 230, 28, 0]], out = "";
    fish.forEach(function (f) {
      var c = css(seen(ORANGE, f[2], "coastal")), s = 1.15 - f[2] / 40, x = f[0], y = f[1];
      out += '<g transform="translate(' + x + " " + y + ") scale(" + s.toFixed(2) + ')"><ellipse cx="0" cy="0" rx="34" ry="11" fill="' + c + '"/><path d="M-30 0 L-48 -12 L-48 12 Z" fill="' + c + '"/><circle cx="22" cy="-3" r="2.2" fill="#03121A"/>' + (f[3] ? '<rect x="-54" y="-18" width="94" height="36" rx="3" fill="none" stroke="#F7B24A" stroke-width="2.2"/>' : "") + "</g>";
    });
    gEl.innerHTML = out;
  }

  /* ---------------- views and routing ---------------- */
  var ANCHOR = { tour: "#lc-tour", five: "#lc-five-sec", course: "#lc-course", capstones: "#lc-capstones", teach: "#lc-teach", glossary: "#lc-glossary", faq: "#lc-faq" };
  function show(sub) {
    sub = (sub || "").toLowerCase();
    var mm = /^m0?([1-9])$/.exec(sub), ov = q('[data-lc-view="overview"]'), mv = q('[data-lc-view="module"]');
    if (mm) {
      var m = MODULES[+mm[1] - 1];
      ov.hidden = true; mv.hidden = false;
      if (current !== m.n) { current = m.n; renderModule(m); }
      window.scrollTo(0, 0);
      document.title = "Module " + pad(m.n) + ": " + m.title + " · Learn · Aquatic Guardian";
      return;
    }
    current = null; mv.hidden = true; ov.hidden = false;
    document.title = "Learn to see underwater · Aquatic Guardian";
    var target = ANCHOR[sub] && q(ANCHOR[sub]);
    if (target) setTimeout(function () { target.scrollIntoView({ block: "start" }); }, 30); else window.scrollTo(0, 0);
  }
  function boot() {
    if (booted) return;
    root = document.getElementById("lc"); if (!root) return;
    state.path = load("path", "all"); if (!PATHS.some(function (p) { return p.id === state.path; })) state.path = "all";
    state.done = load("done", {}); state.quiz = load("quiz", {});
    drawArt(); bindPaths(); renderMap(); bindGlossary(); tourApi = bindTour();
    var pr = q("#lc-print");
    if (pr) pr.addEventListener("click", function () { document.body.classList.add("lc-printing"); window.print(); setTimeout(function () { document.body.classList.remove("lc-printing"); }, 500); });
    booted = true;
  }
  U.inits.learn = function (sub) { boot(); show(sub); };
  U.onRoute.learn = function (sub) { boot(); show(sub); };

  if (standalone) {   // preview without the site router
    var run = function () { var h = (location.hash || "").replace(/^#\/?/, "").split("/"); if (!h[0] || h[0] === "learn") { boot(); show(h[1] || ""); } };
    window.addEventListener("hashchange", run);
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
  }
})();
