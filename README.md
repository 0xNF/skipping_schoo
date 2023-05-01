# Requirements
* Python 3.10+
* FFMpeg



# Installation
`pip install -r requirements.txt`

# Usage

Add your OpenAI API key to the `OPENAI_API_KEY` environment variable before running.

To make the first use of this flow easier, it is recommended to install `faster_whisper` and download the `large-v2` model before running.

This program is intended to be used with Japanese language video. 


# Pipeline
## (1) Downloading a Schoo Video
### `download_schoo.py $url`
Schoo videos are numbered by a `${video_id}`, e.g.,  `2799`

This class number can be used to fetch a `.m3u8` file, which contains a playlist listing tiny pieces of the whole video. This playlist file is automatically downloaded, which then downloads the constituent pieces, and assembles a whole video file automatically into a newly made `./2799` folder.

```bash
download_schoo.py https://schoo.jp/class/2799/room
```

The video file will be at `./2799/2799.mp4`


## (2) Ripping Audio
### `rip_audio.py $video_file`

 Some whisper models prefer the audio output to be in 16khz WAV file format. Additionally, it is better to have Mono, not Stereo, audio. We use FFMPEG to make a mono 16khz wav file from the audio channels.


```bash
rip_audio.py ./2777
 ```

This file takes the input path, given by the output of the `download_schoo` file, and extracts audio into the folder, for example, `./2799/2799.wav`

## (3) Making a Transcription
### `transcribe.py $video_file`

Loads Whisper into VRAM and outputs a transcription of the audio:

```bash
transcribe.py ./2799/2799.wav
```

This will output a text file of the full transcript to `./2799/2799.txt`

## (4) Send to OpenAI for summary
### `summarize.py $transcript_file`

The transcript file will be assessed for its token count, and then sent up to ChatGPT for a bullet point list of summaries. 

If the token count is too large, a folder at `./2799/chunks/` will be created, where each file in that folder is a text document containing tokens, the number of which ChatGPT can handle individually

Each of those chunks will be summarized and placed in the `./2799/summaries` directory.

The list of summaries will then be handed back to ChatGPT for a final summary. The final summary is located at `./2799/2799_summary.txt`

```bash
summarize.py ./2799.txt スマホサイトコーディング入門 -構造設計とHTMLコーディング
```

# Example Output
From the schoo video [スマホサイトコーディング入門 -構造設計とHTMLコーディング](https://schoo.jp/class/2799/room) (_"Introduction to Smartphone Coding - Structuring, Designing, and coding in HTML"_), we extract the following meta-summary of the video:



    1. The course teaches how to code a website optimized for viewing on a smartphone.
    2. No prior coding knowledge is required, making the course accessible to beginners.
    3. Understanding the basics of HTML and CSS is important before diving into more complex topics.
    4. The purpose and goals of the website must be understood before beginning the coding process.
    5. Semantic HTML tags should be used for website structure and proper indentation and commenting in HTML code for readability and easier maintenance.
    6. Responsive design allows websites to adjust their layout based on the screen size of the device being used.
    7. Media queries can be used to adjust the layout of a website based on the size of the screen it is being viewed on.
    8. Proper use of headings is important for website accessibility and search engine optimization.
    9. Appropriate HTML tags, such as \<header>, \<nav>, \<main>, and \<footer>, should be used for content organization and accessibility.
    10. Alt text should be used for images to make them accessible to visually impaired users.
    11. The viewport is the visible area of the device's screen and can be adjusted to fit different screen sizes.
    12. A clear and easy-to-use navigation menu is important for mobile websites.
    13. Images should be optimized for mobile devices to reduce page load time.
    14. CSS can be used for styling mobile websites.
    15. JavaScript can be used to create interactive elements on mobile websites.
    16. Accessibility guidelines and best practices should be followed when designing and coding mobile websites.
    17. Regular testing on different devices is important to ensure the website is functioning properly.


The meta-summary is constructed from a series of intermediate summaries, because the video,s which are often an hour long or more, cannot fit into the token count for ChatGPT. An example of intermediate summaries is the following:


    Snippet 1 of 17 is an introduction to the online course titled "Introduction to Smartphone Site Coding - Structural Design and HTML Coding". The instructor introduces himself and explains the purpose of the course, which is to teach students how to code a website that is optimized for viewing on a smartphone. The course will cover topics such as structural design, HTML coding, and CSS styling. The instructor also mentions that no prior coding knowledge is required, making the course accessible to beginners.  

    Snippet 2 of 17 introduces the instructor and his experience in web design and development. The instructor emphasizes the importance of understanding the basics of HTML and CSS before diving into more complex topics. He also mentions the tools that will be used in the course, such as a text editor and a browser. The instructor encourages students to follow along with the course and practice coding on their own to improve their skills. 

    Snippet 3 of the Japanese language online course "スマホサイトコーディング入門 -構造設計とHTMLコーディング" discusses the importance of understanding the purpose and goals of the website before beginning the coding process. The instructor emphasizes the need to consider the target audience and their needs, as well as the desired user experience. The snippet also touches on the importance of organizing the website\'s structure and content in a logical and user-friendly manner.

    Snippet 4 of the online course "スマホサイトコーディング入門 -構造設計とHTMLコーディング" discusses the importance of using semantic HTML tags for website structure. The instructor explains that semantic tags help search engines and screen readers understand the content of a website, making it more accessible and easier to navigate. Examples of semantic tags include \<header>, \<nav>, \<main>, and \<footer>. The instructor also emphasizes the importance of using proper indentation and commenting in HTML code for readability and easier maintenance.

    Snippet5 introduces the concept of "responsive design" and explains how it allows websites to adjust their layout based on the screen size of the device being used. The instructor also briefly discusses the importance of considering user experience when designing websites for mobile devices.

    Snippet6 of the course discusses the importance of using semantic HTML when coding a website. Semantic HTML refers to using HTML tags that accurately describe the content they contain, making it easier for search engines and screen readers to understand the content. The instructor provides examples of semantic HTML tags such as \<header>, \<nav>, and \<main>, and explains how to use them effectively. Additionally, the instructor emphasizes the importance of avoiding the use of non-semantic tags such as \<div> unless necessary.

    This snippet discusses the importance of responsive design in web development, as more and more people are accessing websites on their mobile devices. The instructor explains how to use media queries to adjust the layout of a website based on the size of the screen it is being viewed on. They also provide some tips for optimizing images for mobile devices, such as using the correct file format and compressing the file size.

    Snippet8 discusses the use of headings in HTML and their importance for website accessibility and search engine optimization. The instructor explains the different levels of headings and how they should be used to structure content on a webpage. The importance of using descriptive and concise headings is emphasized, as well as the need to avoid using headings for decorative purposes only. The instructor also provides examples of how headings can be used to improve the accessibility and usability of a website for all users.

    Snippet9 of 17 discusses the importance of using appropriate HTML tags for content organization and accessibility. The instructor explains how to use semantic HTML tags such as \<header>, \<nav>, \<main>, and \<footer> to structure a webpage and make it easier for screen readers and search engines to understand the content. The instructor also emphasizes the importance of using alt attributes for images to provide text descriptions for visually impaired users.

    Snippet10 of 17 discusses the importance of using semantic HTML tags for better accessibility and search engine optimization. The instructor explains the purpose of different HTML tags, such as \<header>, \<nav>, and \<main>, and how they contribute to the overall structure of a webpage. The instructor also emphasizes the importance of using alt text for images to make them accessible to visually impaired users.

    Snippet11 discusses the use of "viewport" in responsive design. The instructor explains that the viewport is the visible area of the device\'s screen and how it can be adjusted to fit different screen sizes. They also demonstrate how to set the viewport in HTML code using meta tags.

    Snippet12 of the Japanese language online course "スマホサイトコーディング入門 -構造設計とHTMLコーディング" discusses how to create a navigation menu for a mobile website. The instructor explains how to use HTML and CSS to create a simple and functional menu that is easy to navigate on a small screen. The importance of using clear and concise labels for menu items is emphasized, as well as the need to test the menu on different devices to ensure that it works properly.

    Snippet13 discusses how to create a navigation menu for a mobile website. The instructor explains the importance of having a clear and easy-to-use navigation menu, and demonstrates how to create a basic menu using HTML and CSS. They also provide tips on how to make the menu responsive and adjust its appearance for different screen sizes.

    Snippet14 discusses the use of images on mobile websites. The instructor explains that it\'s important to optimize images for mobile devices to reduce page load times and improve user experience. He suggests using the correct file format, compressing images, and using responsive images that adjust to different screen sizes. The instructor also shows how to use the HTML \<picture> tag to display different images based on the device\'s screen size.

    Snippet15 discusses the use of images in website design, including how to optimize them for web use and the importance of considering file size and resolution. The instructor also explains how to use the "alt" attribute to provide alternative text for users who cannot see the images. Finally, the snippet covers the use of CSS to style images, including adding borders and adjusting their position on the page.

    Snippet16 discusses the importance of responsive design in website development. The instructor explains that responsive design allows a website to adapt to different screen sizes and devices, providing a better user experience. They also introduce the concept of media queries, which allow developers to apply different styles to a website based on screen size. The instructor demonstrates how to use media queries in CSS to adjust the layout of a website for different devices.

    Snippet17 is the conclusion of the course, where the instructor thanks the students for taking the course and encourages them to continue learning and practicing. The instructor also reminds the students that coding is a never-ending learning process and that they should not be afraid to make mistakes. The course was designed to provide a foundation for coding mobile websites using HTML and CSS, and the instructor hopes that the students will continue to build on that foundation and create their own unique websites.
