    def start_loader(self,t="●●●"):
        if getattr(self, "loader_active", False):
            return
        
        self.loader_active = True

        # breathing glow color cycle
        self.glow_colors = [
            "#66ffe5", "#33f5d4", "#00e6c5",
            "#00d4b7", "#00c0a5", "#00ad94",
            "#009982", "#008671", "#00735f",
            "#008671", "#009982", "#00ad94",
            "#00c0a5", "#00d4b7", "#00e6c5",
            "#33f5d4"
        ]

        # breathing sizes
        self.glow_sizes = [16,13,10,13,16,13,10,13,16,13,10,13]
                           

        self.loader_step = 0

        # INSERT 3 DOTS ONCE
        self.text_area.configure(state="normal")

        # buffer space to avoid sticking to last message
        self.text_area.insert("end", " ")

        # store start index
        self.loader_start = self.text_area.index("end-1c")

        # insert three dots
        
        self.text_area.insert("end", f"{t}")
        self.loader_end = self.text_area.index("end")

        # apply initial tag for whole loader
        self.text_area.tag_add("loader_tag", self.loader_start, self.loader_end)
        self.text_area.tag_config("loader_tag", foreground="#00ffcc")

        # create per-dot tags
        self.text_area.tag_add("dot1", f"{self.loader_start}", f"{self.loader_start} +1c")
        self.text_area.tag_add("dot2", f"{self.loader_start} +1c", f"{self.loader_start} +2c")
        self.text_area.tag_add("dot3", f"{self.loader_start} +2c", f"{self.loader_start} +3c")

        self.text_area.configure(state="disabled")
        self.text_area.see("end")

        # start animation
        self.animate_loader()


    def animate_loader(self):
        if not self.loader_active:
            return

        # cyclical fade index
        i = self.loader_step

        # each dot breathes at a different offset
        colors = [
            self.glow_colors[i % len(self.glow_colors)],           # dot1
            self.glow_colors[(i + 5) % len(self.glow_colors)],     # dot2
            self.glow_colors[(i + 10) % len(self.glow_colors)],    # dot3
        ]

        sizes = [
            self.glow_sizes[i % len(self.glow_sizes)],             # dot1
            self.glow_sizes[(i + 3) % len(self.glow_sizes)],       # dot2
            self.glow_sizes[(i + 6) % len(self.glow_sizes)],       # dot3
        ]

        self.loader_step += 1

        # update the tags with new glow/fade
        try:
            self.text_area.configure(state="normal")

            # dot1
            self.text_area.tag_config(
                "dot1",
                foreground=colors[0],
                font=("Segoe UI", sizes[0], "bold")
            )
            # dot2
            self.text_area.tag_config(
                "dot2",
                foreground=colors[1],
                font=("Segoe UI", sizes[1], "bold")
            )
            # dot3
            self.text_area.tag_config(
                "dot3",
                foreground=colors[2],
                font=("Segoe UI", sizes[2], "bold")
            )

            self.text_area.configure(state="disabled")
            self.text_area.see("end")

        except:
            pass

        # schedule next frame
        self.root.after(220, self.animate_loader)




    def stop_loader(self):
        self.loader_active = False
        try:
            self.text_area.configure(state="normal")
            self.text_area.delete(self.loader_start, self.loader_end)
            self.text_area.configure(state="disabled")
        except:
            pass