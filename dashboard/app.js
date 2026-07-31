document.addEventListener(
  "click",
  (event) => {
    const tab = event.target.closest(".navbar-collapse .nav-link");
    if (!tab) {
      return;
    }

    const collapse = document.querySelector(".navbar-collapse");
    const toggler = document.querySelector(".navbar-toggler");
    if (!collapse || !toggler) {
      return;
    }

    if (collapse.classList.contains("show")) {
      toggler.click();
    } else if (collapse.classList.contains("collapsing")) {
      collapse.addEventListener(
        "shown.bs.collapse",
        () => {
          toggler.click();
        },
        { once: true },
      );
    }
  },
  true,
);
