--[[ Remove speaker-note blocks from the published build.

     The notes contain the Activity 2 answer key and the instructor's private
     observations. Reveal.js ships them inside the HTML, so anyone who opens
     the deck can press S and read them. This filter is applied only by the
     `public` profile, which is what the GitHub Pages workflow renders.

     Local `quarto render` / `quarto preview` keep the notes. ]]

function Div(el)
  if el.classes:includes("notes") then
    return {}
  end
end
