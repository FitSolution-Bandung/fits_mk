import { Component, useState, useRef, onWillDestroy, status } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { useAutofocus } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class GenerateTextDialog extends Component {
  static template = "fits_management_construction.GenerateTextDialog";
  static component = { Dialog };
  static props = {
    startPrompt: { type: String },
    close: Function,
    insert: Function,
  };

  setup() {
    this.rpc = useService("rpc");
    this.state = useState({
      prompt: "",
      style: "creative",
      format: "article",
      generating: false,
    });
    onWillDestroy(() => this.pendingRpcPromise?.abort());

    this.promptTextRef = useRef("promptText");

    this.notification = useService("notification");

    useAutofocus({ refName: "promptText" });

    this.state.prompt = this.props.startPrompt;
  }

  _buildPrompt() {
    let result =
      "Generative an article about" +
      this.style.prompt +
      "." +
      " " +
      "The writing style should be " +
      this.state.style +
      ".";
    if (this.state.format == "Article") {
      result = result + " " + "To be placed in a web page.";
    } else {
      result =
        result +
        " " +
        "To be placed in a product description of an ecommerce product page.";
    }

    return result;
  }

  _processGeneratedText(content) {
    const lines = content.split("\n").filter((line) => line.trim().length);
    const fragment = document.createDocumentFragment();
    let converter = new showdown.Converter();
    let result = converter.makeHtml(content);
    let el = document.createElement("p");
    el.innerHTML = result;
    fragment.appendChild(el);
    return fragment;
  }

  _cancel() {
    this.props.close();
  }

  _confirm() {
    try {
      const self = this;
      const aiPrompt = this._buildPrompt();

      this.state.generating = true;
      this._generate(aiPrompt, (content, isError) => {
        self.state.generating = false;
        if (!isError) {
          self.props.insert(self._processGeneratedText(content));
          self.props.close();
        } else {
          this.notification.add(content, { type: "error" });
        }
      });
    } catch (e) {
      this.props.close();
      throw e;
    }
  }

  _generate(prompt, callback) {
    const protectedCallback = (...args) => {
      delete this.pendingRpcPromise;
      return callback(...args);
    };
    this.pendingRpcPromise = this.rpc(
      "/fits_management_construction/generate_text",
      {
        prompt: prompt,
      },
      { shadow: true }
    );
    return this.pendingRpcPromise
      .then((content) => protectedCallback(content))
      .catch((error) =>
        protectedCallback(_t(error.data?.message || error.message), true)
      );
  }
}
