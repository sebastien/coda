from templates import h


# TODO: Support with statement
# with h.html as doc:
#     with h.head:
#         with h.style

doc = h.html(
    h.head(
        h.style(
            """
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Jost:wght@300;400;600;800;900&display=swap");

:root {
    padding: 0px;
margin: 0px;
    --color-Gold: "#d5b819";
    --color-BrightGold: "#fcd647";
    --color-bgActive: "#fcebb3";
    --color-bdActive: "#d5b819";
    --font-sans: Jost,sans-serif;
    --font-serif: Martel,serif;
    --H1: "12px";
    --H2: "14px";
    --H3: "16px";
    --H4: "20px";
    --H6: "24px";
}
html,body,object,iframe,h1,h2,h3,h4,h5,h6,p,blockquote,pre,abbr,address,cite,code,del,dfn,em,img,ins,kbd,q,samp,small,strong,sub,sup,var,b,i,dl,dt,dd,ol,ul,li,fieldset,form,label,legend,table,caption,tbody,tfoot,thead,tr,th,td,article,aside,canvas,details,figcaption,figure,footer,header,hgroup,menu,nav,section,summary,time,mark,audio,video {box-sizing: border-box;margin:0;padding:0;border:0;vertical-align:baseline;list-style-type: none;text-rendering:optimizeLegibility;}

html {
    font-family:var(--font-sans);
    font-size: 1rem;
    line-height: 1.25em;
}
body {
    padding: 1.5em;
}
"""
        )
    ),
    h.body(h.h1("Hello, World!")),
)

print("<!DOCTYPE html>")
print(doc)

# EOF
