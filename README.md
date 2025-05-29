<a id="readme-top"></a>
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Unlicense License][license-shield]][license-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/MangarrTeam/Mangarr">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Mangarr</h3>

  <p align="center">
    Manga downloader and manager
    <br />
    <a href="https://github.com/MangarrTeam/Mangarr"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/MangarrTeam/Mangarr/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/MangarrTeam/Mangarr/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Main page example][product-screenshot]]()

Reading manga, manhwa, and mangua often means hopping between multiple websited, each with different layouts, quality, and reading experiences. It can be frustrating to keep track on your favourite series across so many platforms.

**Mangarr** was created to solve that problem.

Mangarr is unified tool that lets you *search*, *download*, and *organize* manga from various sources - all in one place. Whether it's a Japanese manga, a Korean manhwa, or a Chinese manhua, Mangarr helps you bring them together into single, clean library with editable metadata in CBZ files.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Django][Django.com]][Django-url]
* [![Bootstrap][Bootstrap.com]][Bootstrap-url]
* [![JQuery][JQuery.com]][JQuery-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

Follow these steps to set up and run **Mangarr** locally using Docker and Docker Compose.

### Prerequisites

Make sure you have the following installed on your machine

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Installation

You can use this *docker-compose.yml* just replace/define the .env variables *PROJECT_ROOT* and *MANGA_FOLDER*

```yml
services:
  mangarr:
    image: ghcr.io/mangarrteam/mangarr:latest
    container_name: mangarr
    ports:
      - "80:80"
      - "81:81"   # for admin page
    volumes:
      - ${PROJECT_ROOT}:/app/project_root
      - ${MANGA_FOLDER}:/manga/media
    restart: unless-stopped
```



<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Simply open your browser to `http://localhost` (or your device IP address) there if you openned for the first time you will be prompted with registration (this account will be created as server Admin), then you can login with the credentials you entered and start exploring with ease. The interface was made to be easily understanded and easily oriented in so there shouldn't be any problems.

<small>If you are unable to register, you are getting CSRF error, then you need to go to the folder you mounted as *PROJECT_ROOT* there you will see config folder in which is **mangarr.conf** there you will need to add your device IP address to the list under *csrf_trusted_origins* and restart the container</small>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] Add Plugin manager
- [x] Add ability to download manga parsed using plugins
- [ ] Add metadata editor
    - [x] Editor
    - [ ] Saving
- [ ] Multi-language Support
    - [x] Czech
    - [x] English

See the [open issues](https://github.com/MangarrTeam/Mangarr/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions to Mangarr are always welcome! Whether it's bug reports, feature requests, or code improvements, your help makes the project better for everyone.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Plugin contributing

Mangarr supports extending pages compatibility through plugins. If you want to contribute a new plugin for additional manga sources, you can do so easily [here](https://github.com/MangarrTeam/mangarr-plugins)

#### How to contribute a plugin:

- follow the provided [**plugin template**](https://github.com/MangarrTeam/mangarr-plugin) to create your plugin code.
- Visit the [plugin list repo](https://github.com/MangarrTeam/mangarr-plugins) and open issue requesting new plugin


### Top contributors:

<a href="https://github.com/MangarrTeam/Mangarr/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=MangarrTeam/Mangarr" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the Unlicense License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Project Link: [https://github.com/MangarrTeam/Mangarr](https://github.com/MangarrTeam/Mangarr)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Choose an Open Source License](https://choosealicense.com)
* [Malven's Flexbox Cheatsheet](https://flexbox.malven.co/)
* [Malven's Grid Cheatsheet](https://grid.malven.co/)
* [Img Shields](https://shields.io)
* [GitHub Pages](https://pages.github.com)
* [Font Awesome](https://fontawesome.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/MangarrTeam/Mangarr.svg?style=for-the-badge
[contributors-url]: https://github.com/MangarrTeam/Mangarr/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/MangarrTeam/Mangarr.svg?style=for-the-badge
[forks-url]: https://github.com/MangarrTeam/Mangarr/network/members
[stars-shield]: https://img.shields.io/github/stars/MangarrTeam/Mangarr.svg?style=for-the-badge
[stars-url]: https://github.com/MangarrTeam/Mangarr/stargazers
[issues-shield]: https://img.shields.io/github/issues/MangarrTeam/Mangarr.svg?style=for-the-badge
[issues-url]: https://github.com/MangarrTeam/Mangarr/issues
[license-shield]: https://img.shields.io/github/license/MangarrTeam/Mangarr.svg?style=for-the-badge
[license-url]: https://github.com/MangarrTeam/Mangarr/blob/master/LICENSE.txt
[product-screenshot]: images/example.png
[Django.com]: https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=Django&logoColor=white
[Django-url]: https://www.djangoproject.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
