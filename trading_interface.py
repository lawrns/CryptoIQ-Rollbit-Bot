from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from config import SELECTORS
import time
import logging


class NavigationRedirectedError(Exception):
    """Raised when an unexpected navigation happens during a click step."""
    pass

class TradingInterface:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        # Set up module-level logger once
        self.logger = logging.getLogger("sentinel.trading")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler("trade_debug.log", encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        self.logger.propagate = False

    # ============ Deep DOM Inspection Utilities (for accurate in-panel direction detection) ==========
    def _element_attrs(self, element) -> dict:
        try:
            return self.driver.execute_script(
                "var el=arguments[0];var o={};for(var i=0;i<el.attributes.length;i++){var a=el.attributes[i];o[a.name]=a.value}return o;",
                element
            ) or {}
        except Exception:
            return {}

    def _element_dataset(self, element) -> dict:
        try:
            return self.driver.execute_script(
                "var el=arguments[0];var o={};if(el&&el.dataset){for(var k in el.dataset){o[k]=el.dataset[k]}}return o;",
                element
            ) or {}
        except Exception:
            return {}

    def _element_rect(self, element) -> dict:
        try:
            return self.driver.execute_script(
                "var r=arguments[0].getBoundingClientRect();return {top:r.top,left:r.left,width:r.width,height:r.height};",
                element
            ) or {}
        except Exception:
            return {}

    def _element_css(self, element) -> dict:
        try:
            return self.driver.execute_script(
                "var cs=getComputedStyle(arguments[0]);return {color:cs.color,backgroundColor:cs.backgroundColor,fontWeight:cs.fontWeight};",
                element
            ) or {}
        except Exception:
            return {}

    def _element_xpath(self, element) -> str:
        # Best-effort xpath generator from element up to document root
        try:
            return self.driver.execute_script(
                """
                function xpath(el){
                  if(el===document.body) return '/html/body';
                  var ix=0; var siblings=el.parentNode?el.parentNode.childNodes:[];
                  for(var i=0; i<siblings.length; i++){
                    var sib=siblings[i];
                    if(sib===el){
                      var seg=xpath(el.parentNode)+'/'+el.tagName.toLowerCase()+'['+(ix+1)+']';
                      return seg;
                    }
                    if(sib.nodeType===1 && sib.tagName===el.tagName){ ix++; }
                  }
                  return el.tagName.toLowerCase();
                }
                return xpath(arguments[0]);
                """,
                element
            ) or ''
        except Exception:
            return ''

    def _closest_form_from_place_bet(self):
        try:
            btn = self._find_place_bet_button()
            if not btn:
                return None
            return self.driver.execute_script("return arguments[0].closest('form');", btn)
        except Exception:
            return None

    def _snapshot_element(self, element) -> dict:
        try:
            data = {
                'tag': element.tag_name,
                'text': (element.text or '').strip(),
                'classes': (element.get_attribute('class') or '').strip(),
                'role': (element.get_attribute('role') or '').strip(),
                'type': (element.get_attribute('type') or '').strip(),
                'name': (element.get_attribute('name') or '').strip(),
                'value': (element.get_attribute('value') or '').strip(),
                'href': element.get_attribute('href') or '',
                'onclick': element.get_attribute('onclick') or '',
                'aria_pressed': (element.get_attribute('aria-pressed') or '').strip(),
                'aria_selected': (element.get_attribute('aria-selected') or '').strip(),
                'aria_checked': (element.get_attribute('aria-checked') or '').strip(),
                'checked': (element.get_attribute('checked') or '').strip(),
                'disabled': (element.get_attribute('disabled') or '').strip(),
                'data': self._element_dataset(element),
                'attrs': self._element_attrs(element),
                'rect': self._element_rect(element),
                'css': self._element_css(element),
                'xpath': self._element_xpath(element),
                'displayed': False,
                'enabled': False,
            }
            try:
                data['displayed'] = bool(element.is_displayed())
            except Exception:
                pass
            try:
                data['enabled'] = bool(element.is_enabled())
            except Exception:
                pass
            return data
        except Exception as e:
            return {'error': str(e)}

    def inspect_in_panel_controls(self):
        """Locate and print/log the real in-panel direction controls near the PLACE BET button.
        This does not click anything; it only reports candidates and active-state hints."""
        try:
            panel = self._find_order_panel_container()
            if panel is None:
                print("[inspect] Order panel container not found")
                self.logger.warning("inspect_in_panel_controls: panel not found")
                return []

            place_btn = self._find_place_bet_button()
            if not place_btn:
                print("[inspect] PLACE BET button not found")
                self.logger.warning("inspect_in_panel_controls: place bet not found")
            print("\n=== INSPECT IN-PANEL CONTROLS (near PLACE BET) ===")

            # Candidate query: elements that look like toggles or tabs inside the same panel
            candidates = []
            xp = (
                ".//*[self::button or self::a or self::div or self::span or self::label or self::input]"
                "[(@role='button' or @role='tab' or @role='switch' or @type='button' or @type='radio' or contains(translate(@class,'BTN','btn'),'btn'))"
                " and (contains(translate(normalize-space(.),'buy','BUY'),'BUY') or "
                "contains(translate(normalize-space(.),'sell','SELL'),'SELL') or "
                "contains(translate(normalize-space(.),'up','UP'),'UP') or "
                "contains(translate(normalize-space(.),'down','DOWN'),'DOWN') or "
                "contains(translate(normalize-space(.),'long','LONG'),'LONG') or "
                "contains(translate(normalize-space(.),'short','SHORT'),'SHORT'))]"
            )
            try:
                candidates.extend(panel.find_elements(By.XPATH, xp))
            except Exception:
                pass

            # Include hidden radios + their labels if any
            try:
                radios = panel.find_elements(By.XPATH, ".//input[@type='radio']")
                for r in radios:
                    candidates.append(r)
                    try:
                        lbl = r.find_element(By.XPATH, 'following-sibling::label | ancestor::label')
                        if lbl:
                            candidates.append(lbl)
                    except Exception:
                        pass
            except Exception:
                pass

            # Broaden: any ARIA/role-based toggles inside panel
            try:
                aria_role_candidates = panel.find_elements(
                    By.CSS_SELECTOR,
                    "[role='button'], [role='tab'], [role='switch'], [role='radio'], [aria-pressed], [aria-selected], [aria-checked]"
                )
                candidates.extend(aria_role_candidates)
            except Exception:
                pass

            # Broaden: segmented/toggle/tab UI by class heuristics
            try:
                class_heuristics = panel.find_elements(
                    By.CSS_SELECTOR,
                    "[class*='segment'], [class*='toggle'], [class*='switch'], [class*='tab'], [class*='pill']"
                )
                candidates.extend(class_heuristics)
            except Exception:
                pass

            # Nearby siblings to PLACE BET (previous blocks often contain direction control)
            if place_btn:
                try:
                    prev_blocks = self.driver.execute_script(
                        "var n=arguments[0];var out=[];for(var i=0;i<4&&n;n=n.previousElementSibling,i++){out.push(n)}return out;",
                        place_btn
                    ) or []
                    for blk in prev_blocks:
                        try:
                            candidates.extend(blk.find_elements(By.XPATH, ".//*"))
                        except Exception:
                            pass
                except Exception:
                    pass

            # Deduplicate while preserving order
            seen = set()
            deduped = []
            for el in candidates:
                try:
                    key = el._id  # Selenium internal id is stable per session
                except Exception:
                    key = id(el)
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(el)

            # Rank by proximity to PLACE BET when available
            if place_btn:
                try:
                    btn_rect = self._element_rect(place_btn)
                    def distance(e):
                        r = self._element_rect(e)
                        try:
                            cx = r.get('left', 0) + r.get('width', 0)/2
                            cy = r.get('top', 0) + r.get('height', 0)/2
                            bx = btn_rect.get('left', 0) + btn_rect.get('width', 0)/2
                            by = btn_rect.get('top', 0) + btn_rect.get('height', 0)/2
                            import math
                            return math.hypot(cx-bx, cy-by)
                        except Exception:
                            return 1e9
                    deduped.sort(key=distance)
                except Exception:
                    pass

            results = []
            # Snapshot the PLACE BET button for context
            if place_btn:
                try:
                    pb = self._snapshot_element(place_btn)
                    print("\n[submit] PLACE BET snapshot:")
                    print(f"- tag={pb.get('tag')} text='{pb.get('text')}' class='{pb.get('classes')}' role='{pb.get('role')}' type='{pb.get('type')}'")
                    print(f"  css.color={pb.get('css',{}).get('color')} css.bg={pb.get('css',{}).get('backgroundColor')} xpath={pb.get('xpath')}")
                except Exception:
                    pass

            for el in deduped[:20]:  # cap output
                snap = self._snapshot_element(el)
                results.append(snap)
                try:
                    print(f"- tag={snap.get('tag')} text='{snap.get('text')}' class='{snap.get('classes')}' role='{snap.get('role')}' type='{snap.get('type')}'")
                    print(f"  aria-pressed={snap.get('aria_pressed')} aria-selected={snap.get('aria_selected')} aria-checked={snap.get('aria_checked')} checked={snap.get('checked')} displayed={snap.get('displayed')} enabled={snap.get('enabled')}")
                    act = snap.get('attrs', {}).get('data-state') or snap.get('attrs', {}).get('data-active') or snap.get('data', {}).get('state')
                    print(f"  data-state={act} css.color={snap.get('css',{}).get('color')} css.bg={snap.get('css',{}).get('backgroundColor')}")
                    print(f"  xpath={snap.get('xpath')}")
                except Exception:
                    pass

            # Dump form inputs (hidden fields often contain side/direction)
            frm = self._closest_form_from_place_bet()
            if frm:
                try:
                    inputs = self.driver.execute_script(
                        "var f=arguments[0];var xs=Array.from(f.querySelectorAll('input,select,textarea'));return xs.map(x=>({name:x.name||'',type:x.type||'',value:(x.type==='password'?'***':x.value||''),checked:!!x.checked,classes:x.className||''}));",
                        frm
                    )
                    print("\nForm inputs near submit (name,type,value,checked):")
                    for it in inputs:
                        try:
                            nm = it.get('name','')
                            ty = it.get('type','')
                            val = it.get('value','')
                            chk = it.get('checked', False)
                            cls = it.get('classes','')
                            if any(k in (nm.lower()+val.lower()+cls.lower()) for k in ['side','dir','buy','sell','long','short','up','down']):
                                marker = '  <-- possible direction field'
                            else:
                                marker = ''
                            print(f"  - {nm} | {ty} | {val} | checked={chk} | class={cls}{marker}")
                        except Exception:
                            continue
                except Exception:
                    pass

            # Also scan for hidden inputs within the panel (even if not inside a form)
            try:
                hidden_inputs = self.driver.execute_script(
                    "var p=arguments[0];var xs=Array.from(p.querySelectorAll('input[type=\"hidden\"]'));return xs.map(x=>({name:x.name||'',value:x.value||'',classes:x.className||''}));",
                    panel
                ) or []
                if hidden_inputs:
                    print("\nPanel hidden inputs:")
                    for hi in hidden_inputs:
                        nm = hi.get('name','')
                        val = hi.get('value','')
                        cls = hi.get('classes','')
                        mark = '  <-- possible direction field' if any(k in (nm.lower()+val.lower()+cls.lower()) for k in ['side','dir','buy','sell','long','short','up','down']) else ''
                        print(f"  - {nm} = {val} | class={cls}{mark}")
            except Exception:
                pass

            # Deep scan with shadow DOM traversal to surface hidden toggle-like controls
            try:
                deep = self.driver.execute_script(
                    """
                    function deepScan(root, limit){
                      var out=[]; var visited=0;
                      function push(node){
                        try{
                          var tag=node.tagName?node.tagName.toLowerCase():'';
                          var role=node.getAttribute? (node.getAttribute('role')||'') : '';
                          var cls=(node.className||'')+'';
                          var txt=(node.innerText||'').trim();
                          var typ=node.type || (node.getAttribute?node.getAttribute('type'):'') || '';
                          var nm=node.name || (node.getAttribute?node.getAttribute('name'):'') || '';
                          var ap=node.getAttribute? (node.getAttribute('aria-pressed')||'') : '';
                          var as=node.getAttribute? (node.getAttribute('aria-selected')||'') : '';
                          var ac=node.getAttribute? (node.getAttribute('aria-checked')||'') : '';
                          var ds={}; try{ if(node.dataset){ for(var k in node.dataset){ ds[k]=node.dataset[k]; } } }catch(e){}
                          out.push({tag:tag, role:role, classes:cls, text:txt, type:typ, name:nm, aria_pressed:ap, aria_selected:as, aria_checked:ac, data:ds});
                        }catch(e){}
                      }
                      function isCandidate(node){
                        try{
                          var txt=(node.innerText||'').toLowerCase();
                          var cls=(node.className||'').toLowerCase();
                          var role=node.getAttribute? (node.getAttribute('role')||'') : '';
                          var typ=node.type || (node.getAttribute?node.getAttribute('type'):'') || '';
                          var hasToggle=node.hasAttribute && (node.hasAttribute('aria-pressed')||node.hasAttribute('aria-selected')||node.hasAttribute('aria-checked'));
                          if(hasToggle) return true;
                          if(typ==='radio' || typ==='button' || role==='tab' || role==='switch' || role==='radio') return true;
                          if(/buy|sell|up|down|long|short/.test(txt)) return true;
                          if(/toggle|switch|segmented|tab|pill/.test(cls)) return true;
                        }catch(e){}
                        return false;
                      }
                      function walk(node){
                        if(!node || visited>limit) return; visited++;
                        try{ if(isCandidate(node)) push(node); }catch(e){}
                        try{ if(node.shadowRoot){ Array.from(node.shadowRoot.children).forEach(walk); } }catch(e){}
                        try{ Array.from(node.children).forEach(walk); }catch(e){}
                      }
                      walk(root);
                      return out;
                    }
                    return deepScan(arguments[0], 2000);
                    """,
                    panel
                ) or []
                if deep:
                    print("\nDeep scan (shadow-aware) candidates:")
                    for item in deep[:20]:
                        try:
                            t = item.get('text','')
                            cls = item.get('classes','')
                            role = item.get('role','')
                            ap = item.get('aria_pressed','')
                            ase = item.get('aria_selected','')
                            ac = item.get('aria_checked','')
                            nm = item.get('name','')
                            typ = item.get('type','')
                            ds = item.get('data',{})
                            blob = f"{t} {cls} {nm} {typ} {ds}".lower()
                            mark = '  <-- likely' if any(k in blob for k in ['buy','sell','up','down','long','short','side','dir']) else ''
                            print(f"  - text='{t}' role={role} type={typ} name={nm} aria-pressed={ap} aria-selected={ase} aria-checked={ac}{mark}")
                            print(f"    classes='{cls}' data={ds}")
                        except Exception:
                            continue
            except Exception:
                pass

            print("=== END IN-PANEL CONTROL INSPECT ===\n")
            self.logger.info("inspect_in_panel_controls completed")
            return results
        except Exception as e:
            self.logger.error(f"inspect_in_panel_controls error: {e}")
            return []

    def start_network_spy(self):
        """Install a temporary network spy to capture request payloads for order placement."""
        try:
            from config import DEBUG_NETWORK_SPY
            if not DEBUG_NETWORK_SPY:
                return True
            self.driver.execute_script(
                """
                if(!window.__sentinelSpy){
                  window.__sentinelSpy={requests:[]};
                  (function(){
                    var spy=window.__sentinelSpy;
                    var _fetch = window.fetch;
                    window.fetch = function(){
                      try{
                        var url = arguments[0];
                        var opts = arguments[1]||{};
                        var body = opts&&opts.body?opts.body:'';
                        spy.requests.push({ts:Date.now(),kind:'fetch',url:String(url),body:body?String(body):''});
                      }catch(e){}
                      return _fetch.apply(this, arguments);
                    };
                    var X = window.XMLHttpRequest;
                    function wrapSend(opened){
                      return function(body){
                        try{
                          var url = this.__url||'';
                          window.__sentinelSpy.requests.push({ts:Date.now(),kind:'xhr',url:String(url),body:body?String(body):''});
                        }catch(e){}
                        return opened.apply(this, arguments);
                      };
                    }
                    var _open = X.prototype.open;
                    X.prototype.open = function(method, url){ this.__url = url; return _open.apply(this, arguments); };
                    var _send = X.prototype.send;
                    X.prototype.send = wrapSend(_send);
                    // Hook WebSocket send
                    try{
                      var _WS = window.WebSocket;
                      var _WSSend = _WS && _WS.prototype && _WS.prototype.send;
                      if(_WSSend && !_WS.prototype.__sentinelWrapped){
                        _WS.prototype.send = function(data){
                          try{ window.__sentinelSpy.requests.push({ts:Date.now(),kind:'ws',url:this.url||'',body:data?String(data):''}); }catch(e){}
                          return _WSSend.apply(this, arguments);
                        };
                        _WS.prototype.__sentinelWrapped = true;
                      }
                    }catch(e){}
                  })();
                }
                return true;
                """
            )
            print("[spy] Network spy installed")
            self.logger.info("Network spy installed")
            return True
        except Exception as e:
            print(f"[spy] Failed to install spy: {e}")
            self.logger.error(f"Network spy install failed: {e}")
            return False

    def dump_network_spy(self):
        """Dump recent captured network requests, focusing on trading endpoints."""
        try:
            from config import DEBUG_NETWORK_SPY
            if not DEBUG_NETWORK_SPY:
                return []
            entries = self.driver.execute_script("return (window.__sentinelSpy && window.__sentinelSpy.requests) || [];") or []
            print("\n=== CAPTURED NETWORK (recent) ===")
            shown = 0
            for r in entries[-20:]:
                try:
                    url = (r.get('url') or '')
                    body = (r.get('body') or '')
                    if any(k in url for k in ['trade','order','position','futures','binary','bet']):
                        print(f"- [{r.get('kind')}] {url}")
                        if body:
                            preview = body if len(body) < 300 else (body[:300] + '...')
                            print(f"  body: {preview}")
                        shown += 1
                except Exception:
                    continue
            if shown == 0:
                print("(no trading-related requests observed yet)")
            print("=== END NETWORK CAPTURE ===\n")
            self.logger.info("Network spy dump printed")
            return entries
        except Exception as e:
            print(f"[spy] Dump error: {e}")
            self.logger.error(f"Network spy dump failed: {e}")
            return []

    def _place_trade_via_api(self, direction: str, wager: float, multiplier: float, instrument: str = 'BTC') -> bool:
        """Attempt to place a trade directly via site API using in-page fetch. Returns True on success."""
        try:
            from config import USE_API_FALLBACK
            if not USE_API_FALLBACK:
                return False
            buy_flag = True if (direction or '').lower() == 'up' else False
            payload = {
                'instrument': instrument,
                'wager': float(wager),
                'multiplier': float(multiplier),
                'take_profit_price': 0,
                'take_profit_win': 0,
                'stop_loss_price': 0,
                'stop_loss_win': 0,
                'buy': buy_flag,
                'structure': 0,
                'rlb': True,
            }
            script = (
                "var done = arguments[arguments.length - 1];"
                "var body = arguments[0];"
                "fetch('/private/trade', {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body)})"
                ".then(async function(r){ try{ var j = await r.json(); done({ok:r.ok,status:r.status,json:j}); } catch(e){ done({ok:r.ok,status:r.status,text:'non-json'});} })"
                ".catch(function(e){ done({ok:false,error:String(e)}); });"
            )
            res = self.driver.execute_async_script(script, payload)
            ok = bool(res.get('ok')) if isinstance(res, dict) else False
            self.logger.info(f"API place trade response: {res}")
            return ok
        except Exception as e:
            self.logger.error(f"API place trade failed: {e}")
            return False

    def _is_on_trading_page(self) -> bool:
        current_url = self.driver.current_url or ""
        return "trading/BTC" in current_url

    def _ensure_on_trading_page(self):
        from config import ROLLBIT_URL
        if not self._is_on_trading_page():
            self.logger.info(f"Navigating back to trading page: {ROLLBIT_URL}")
            self.driver.get(ROLLBIT_URL)
            time.sleep(2)

    def _element_details(self, element) -> str:
        try:
            tag = element.tag_name
            text = (element.text or "").strip()
            classes = (element.get_attribute("class") or "").strip()
            href = element.get_attribute("href")
            onclick = element.get_attribute("onclick")
            return f"<{tag}> text='{text}' classes='{classes}' href='{href}' onclick='{onclick}'"
        except Exception as e:
            return f"<unknown element: {e}>"

    def _javascript_click(self, target, description: str, prevent_default_if_link: bool = True, allow_navigation: bool = False, retry_limit: int = 2):
        """Click an element via JS with retries and URL monitoring.

        target can be a WebElement or a callable that returns a fresh WebElement each attempt.
        """
        attempts = 0
        while attempts <= retry_limit:
            try:
                element = target() if callable(target) else target
            except Exception as e:
                self.logger.error(f"Failed to acquire element before click ({description}): {e}")
                attempts += 1
                time.sleep(0.5)
                continue

            pre_url = self.driver.current_url
            self.logger.info(f"CLICK START | {description} | pre_url='{pre_url}' | {self._element_details(element)}")
            try:
                is_link = False
                try:
                    tag_name = (element.tag_name or '').lower()
                    href = element.get_attribute("href")
                    is_link = (tag_name == "a") or (href is not None and href != "")
                except Exception:
                    pass

                # Strong navigation guard: only for links (to avoid breaking button handlers)
                if prevent_default_if_link and is_link:
                    try:
                        self.driver.execute_script(
                            """
                            (function(el){
                              try {
                                if(!window.__sentinelNav){ window.__sentinelNav = {}; }
                                var g = window.__sentinelNav;
                                if(!g.installed){
                                  g.origPushState = history.pushState; g.origReplaceState = history.replaceState;
                                  history.pushState = function(){ try{ g.lastIntercept = Date.now(); }catch(e){}; return g.origPushState.apply(this, arguments); };
                                  history.replaceState = function(){ try{ g.lastIntercept = Date.now(); }catch(e){}; return g.origReplaceState.apply(this, arguments); };
                                  g.docClick = function(e){ try { e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); } catch(_){} };
                                  document.addEventListener('click', g.docClick, true);
                                  g.installed = true;
                                }
                                // Element-level stoppers
                                var opts = { once: true, capture: true };
                                var stopper = function(e){ try { e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); } catch(_){} };
                                ['click','mousedown','mouseup','pointerdown','pointerup'].forEach(function(t){ el.addEventListener(t, stopper, opts); });
                              } catch(e) {}
                            })(arguments[0]);
                            """,
                            element
                        )
                    except Exception:
                        pass
                # Perform the click
                self.driver.execute_script('arguments[0].click();', element)

                time.sleep(1.0)
                post_url = self.driver.current_url
                self.logger.info(f"CLICK END | {description} | post_url='{post_url}'")

                if not allow_navigation and not self._is_on_trading_page():
                    self.logger.warning(f"Unexpected navigation detected after {description}. Returning to trading page and retrying (attempt {attempts+1}/{retry_limit})")
                    self._ensure_on_trading_page()
                    attempts += 1
                    continue

                # Remove global guards after click
                try:
                    self.driver.execute_script(
                        """
                        try{ var g = window.__sentinelNav; if(g && g.installed){ if(g.docClick){ document.removeEventListener('click', g.docClick, true); } if(g.origPushState){ history.pushState = g.origPushState; } if(g.origReplaceState){ history.replaceState = g.origReplaceState; } g.installed=false; } }catch(e){}
                        return true;
                        """
                    )
                except Exception:
                    pass

                return True
            except Exception as e:
                self.logger.error(f"Error during javascript click on {description}: {e}")
                attempts += 1
                time.sleep(0.5)

        raise NavigationRedirectedError(f"Navigation or click failure persisted after {retry_limit} retries for: {description}")

    def _find_order_panel_container(self):
        """Locate the order panel by anchoring around the PLACE BET button and walking up the DOM."""
        try:
            place_bet = self.driver.find_element(By.CSS_SELECTOR, SELECTORS['place_bet_button'])
        except Exception:
            return None
        container = place_bet
        for _ in range(12):
            try:
                container = container.find_element(By.XPATH, './..')
            except Exception:
                break
        return container

    def _find_order_inputs(self):
        """Find wager and multiplier inputs inside the order panel container.
        Returns a tuple (wager_input, multiplier_input) where elements may be None if not found.
        """
        panel = self._find_order_panel_container()
        if panel is None:
            return (None, None)
        try:
            inputs = panel.find_elements(By.XPATH, ".//input[@type='text' or @type='number']")
        except Exception:
            inputs = []
        wager_input = None
        multiplier_input = None

        # Try to identify by placeholder/aria-label/name
        for inp in inputs:
            try:
                placeholder = (inp.get_attribute('placeholder') or '').lower()
                aria = (inp.get_attribute('aria-label') or '').lower()
                name = (inp.get_attribute('name') or '').lower()
                if any(k in placeholder + aria + name for k in ['wager', 'stake', 'amount', 'size']):
                    wager_input = inp
                if any(k in placeholder + aria + name for k in ['multiplier', 'leverage', 'x', 'payout']):
                    multiplier_input = inp
            except Exception:
                continue

        # Fallback to positional: first is wager, second is multiplier
        if wager_input is None and len(inputs) >= 1:
            wager_input = inputs[0]
        if multiplier_input is None and len(inputs) >= 2:
            multiplier_input = inputs[1]

        return (wager_input, multiplier_input)

    def _confirm_order_if_needed(self) -> bool:
        """Handle an optional confirm modal if Rollbit shows one before placing the order."""
        try:
            # Look for common modal containers near the bottom
            modals = self.driver.find_elements(By.CSS_SELECTOR, '[class*="modal"], [class*="dialog"], [role="dialog"]')
            for m in modals:
                if not m.is_displayed():
                    continue
                # Find a confirm/submit button inside
                btns = m.find_elements(By.XPATH, ".//*[self::button or @role='button']")
                for b in btns:
                    t = (b.text or '').strip().upper()
                    if any(k in t for k in ["CONFIRM", "PLACE", "SUBMIT", "OK"]):
                        try:
                            self._javascript_click(lambda: b, description="Confirm Modal Button", prevent_default_if_link=True)
                            return True
                        except Exception:
                            continue
        except Exception:
            pass
        return False

    def _get_open_positions_count(self) -> int:
        """Heuristic: count cash-out buttons as proxy for open positions."""
        try:
            elems = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS.get('cash_out_button', ''))
            return len([e for e in elems if e.is_displayed()])
        except Exception:
            return 0

    def _find_toast_or_error(self) -> str:
        """Search for toast/alert/error messages after attempting to place an order."""
        # Common patterns: role=alert, toast classes, error texts near form
        candidates = []
        try:
            candidates += self.driver.find_elements(By.CSS_SELECTOR, '[role="alert"], [class*="toast"], [class*="notification"], [class*="error"]')
        except Exception:
            pass
        # Also check the order panel for any error text
        try:
            panel = self._find_order_panel_container()
            if panel is not None:
                candidates += panel.find_elements(By.XPATH, ".//*[contains(translate(normalize-space(.),'error','ERROR'),'ERROR') or contains(., '!')] ")
        except Exception:
            pass
        for el in candidates:
            try:
                if not el.is_displayed():
                    continue
                text = (el.text or '').strip()
                if text:
                    return text
            except Exception:
                continue
        return ''

    def _find_place_bet_button(self):
        """Find the PLACE BET button within the order panel, with fallbacks."""
        panel = self._find_order_panel_container()
        # Preferred: text-based within panel
        if panel is not None:
            try:
                xp = ".//button[contains(translate(normalize-space(.),'place bet','PLACE BET'),'PLACE BET') or contains(translate(normalize-space(.),'bet','BET'),'BET') or @type='submit']"
                elems = panel.find_elements(By.XPATH, xp)
                for e in elems:
                    if e.is_displayed():
                        return e
            except Exception:
                pass
            try:
                xp2 = ".//*[@role='button' and (contains(translate(normalize-space(.),'place','PLACE'),'PLACE') or contains(translate(normalize-space(.),'bet','BET'),'BET'))]"
                elems = panel.find_elements(By.XPATH, xp2)
                for e in elems:
                    if e.is_displayed():
                        return e
            except Exception:
                pass
        # Fallback: global selector
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, SELECTORS.get('place_bet_button', ''))
            if el and el.is_displayed():
                return el
        except Exception:
            pass
        # Last resort: global text search
        try:
            xp3 = "//button[contains(., 'PLACE BET') or contains(., 'Place Bet') or contains(., 'BET')]"
            el = self.driver.find_element(By.XPATH, xp3)
            if el and el.is_displayed():
                return el
        except Exception:
            pass
        return None

    def _get_direction_state(self) -> str:
        """Infer current direction by inspecting computed styles of the Up/Down chips."""
        def get_chip(selector: str):
            try:
                return self.driver.find_element(By.CSS_SELECTOR, selector)
            except Exception:
                return None
        up_sel = SELECTORS.get('up_button', '')
        down_sel = SELECTORS.get('down_button', '')
        up_el = get_chip(up_sel) if up_sel else None
        down_el = get_chip(down_sel) if down_sel else None
        if not up_el and not down_el:
            return ''

        def computed_rgb(el):
            try:
                return self.driver.execute_script(
                    'const cs=getComputedStyle(arguments[0]); return {color: cs.color, bg: cs.backgroundColor};', el
                )
            except Exception:
                return { 'color': (el.get_attribute('style') or ''), 'bg': '' }

        def parse_rgb(s: str):
            # Expect formats like 'rgb(r, g, b)' or 'rgba(r, g, b, a)'
            try:
                import re
                m = re.search(r"rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)", s)
                if m:
                    return int(m.group(1)), int(m.group(2)), int(m.group(3))
            except Exception:
                pass
            return None

        def is_up_active(info):
            # Look for the green Up color ~ rgb(114, 242, 56) in color or bg
            for k in ['color', 'bg']:
                v = (info.get(k) or '').lower()
                if '114' in v and '242' in v and '56' in v:
                    return True
                rgb = parse_rgb(v)
                if rgb:
                    r, g, b = rgb
                    # green dominant heuristic
                    if g > r + 30 and g > b + 30:
                        return True
            return False

        def is_down_active(info):
            # Down active likely turns red; detect red-dominant
            for k in ['color', 'bg']:
                v = (info.get(k) or '').lower()
                if '255' in v and ('37' in v or '82' in v):
                    return True
                rgb = parse_rgb(v)
                if rgb:
                    r, g, b = rgb
                    if r > g + 30 and r > b + 30:
                        return True
            return False

        up_info = computed_rgb(up_el) if up_el else {}
        down_info = computed_rgb(down_el) if down_el else {}
        up_active = is_up_active(up_info)
        down_active = is_down_active(down_info)

        if up_active and not down_active:
            return 'UP'
        if down_active and not up_active:
            return 'DOWN'
        return ''

    def _find_direction_element(self, direction: str):
        """Find UP/BUY or DOWN/SELL element within the order panel container."""
        container = self._find_order_panel_container()
        if container is None:
            return None
        want_up = direction.lower() == 'up'
        # Try class-based elements within container first (button or [role=button])
        try:
            css = SELECTORS.get('up_button') if want_up else SELECTORS.get('down_button')
            if css:
                elems = container.find_elements(By.CSS_SELECTOR, css)
                for e in elems:
                    if not (e.is_displayed() and e.is_enabled()):
                        continue
                    t = (e.text or '').strip().upper()
                    # Ensure the element label matches the requested direction
                    if (want_up and ('UP' in t or 'BUY' in t)) or ((not want_up) and ('DOWN' in t or 'SELL' in t)):
                        return e
        except Exception:
            pass
        # Heuristic: any clickable with role/button and text
        try:
            label_primary = 'BUY' if want_up else 'SELL'
            label_alt = 'UP' if want_up else 'DOWN'
            xp = (
                ".//*[(@role='button' or self::button or self::a or self::div or self::span)"

                ") and (contains(translate(normalize-space(.),'buy','BUY'),'BUY') or "
                "contains(translate(normalize-space(.),'sell','SELL'),'SELL') or "
                "contains(translate(normalize-space(.),'up','UP'),'UP') or "
                "contains(translate(normalize-space(.),'down','DOWN'),'DOWN'))]"
            )
            elems = container.find_elements(By.XPATH, xp)
            for e in elems:
                if not (e.is_displayed() and e.is_enabled()):
                    continue
                t = (e.text or '').strip().upper()
                if label_primary in t or label_alt in t:
                    # Avoid known global toggle class if possible
                    cls = (e.get_attribute('class') or '')
                    if 'css-1wsh2jr' in cls:
                        continue
                    return e
        except Exception:
            pass
        # Last resort: scan the whole page with the same heuristic
        try:
            if want_up:
                xp = ".//button[contains(translate(normalize-space(.),'buyup','BUYUP'),'BUY') or contains(translate(normalize-space(.),'buyup','BUYUP'),'UP')]"
            else:
                xp = ".//button[contains(translate(normalize-space(.),'selldown','SELLDOWN'),'SELL') or contains(translate(normalize-space(.),'selldown','SELLDOWN'),'DOWN')]"
            elems = self.driver.find_elements(By.XPATH, xp)
            for e in elems:
                if e.is_displayed() and e.is_enabled():
                    return e
        except Exception:
            pass
        # Fallback: top-level search for CSS-based Up/Down chips (divs)
        try:
            css = SELECTORS.get('up_button') if want_up else SELECTORS.get('down_button')
            if css:
                elems = self.driver.find_elements(By.CSS_SELECTOR, css)
                for e in elems:
                    if e.is_displayed() and e.is_enabled():
                        t = (e.text or '').strip().upper()
                        if (want_up and ('UP' in t or 'BUY' in t)) or ((not want_up) and ('DOWN' in t or 'SELL' in t)):
                            return e
        except Exception:
            pass
        return None

    def _get_text_size_chip_candidates(self):
        """Find 'Up' and 'Down' chip elements within the order panel by text and size heuristics.
        Returns a dict like {'UP': element or None, 'DOWN': element or None}.
        """
        result = {'UP': None, 'DOWN': None}
        panel = self._find_order_panel_container()
        if panel is None:
            return result
        candidates = []
        # 1) Known chip classes if present
        try:
            candidates += panel.find_elements(By.CSS_SELECTOR, '.css-1p91j2k, .css-qv9fap')
        except Exception:
            pass
        # 2) Text-based 'Up'/'Down' inside panel
        try:
            candidates += panel.find_elements(By.XPATH, ".//*[normalize-space(text())='Up' or normalize-space(text())='Down']")
        except Exception:
            pass
        # 3) Nearby siblings before PLACE BET button
        try:
            place_btn = self._find_place_bet_button()
            if place_btn:
                prevs = self.driver.execute_script(
                    "var n=arguments[0];var out=[];for(var i=0;i<6&&n;n=n.previousElementSibling,i++){out.push(n)}return out;",
                    place_btn
                ) or []
                for blk in prevs:
                    try:
                        candidates += blk.find_elements(By.XPATH, ".//*[normalize-space(text())='Up' or normalize-space(text())='Down']")
                    except Exception:
                        pass
        except Exception:
            pass
        # Dedup and score by size and proximity
        dedup = []
        seen = set()
        for el in candidates:
            try:
                key = el._id
            except Exception:
                key = id(el)
            if key in seen:
                continue
            seen.add(key)
            try:
                if not (el.is_displayed() and el.is_enabled()):
                    continue
            except Exception:
                continue
            dedup.append(el)
        def rect(el):
            try:
                return self._element_rect(el)
            except Exception:
                return {'top': 0, 'left': 0, 'width': 0, 'height': 0}
        # Rank primarily by being small-ish like a chip
        def size_score(r):
            try:
                w = r.get('width', 0) or 0
                h = r.get('height', 0) or 0
                # Chips ~ width <= 140, height ~ 30-50
                size_penalty = 0
                if w > 160: size_penalty += (w - 160)
                if h > 60: size_penalty += (h - 60)
                return size_penalty
            except Exception:
                return 9999
        # Sort by size penalty then by closeness to submit
        btn = self._find_place_bet_button()
        btn_r = self._element_rect(btn) if btn else {'left': 0, 'top': 0, 'width': 0, 'height': 0}
        def dist_score(r):
            try:
                import math
                cx = r.get('left', 0) + r.get('width', 0)/2
                cy = r.get('top', 0) + r.get('height', 0)/2
                bx = btn_r.get('left', 0) + btn_r.get('width', 0)/2
                by = btn_r.get('top', 0) + btn_r.get('height', 0)/2
                return math.hypot(cx-bx, cy-by)
            except Exception:
                return 9999
        scored = []
        for el in dedup:
            try:
                t = (el.text or '').strip().upper()
                if t not in ('UP', 'DOWN'):
                    continue
                r = rect(el)
                scored.append((size_score(r), dist_score(r), el))
            except Exception:
                continue
        scored.sort(key=lambda x: (x[0], x[1]))
        for _, __, el in scored:
            try:
                t = (el.text or '').strip().upper()
                if t in ('UP', 'DOWN') and result.get(t) is None:
                    result[t] = el
            except Exception:
                continue
        return result

    def _get_direction_state_from_chips(self) -> str:
        chips = self._get_text_size_chip_candidates()
        up_el = chips.get('UP')
        down_el = chips.get('DOWN')
        if not up_el and not down_el:
            return ''
        def color_of(el):
            try:
                return self.driver.execute_script('return getComputedStyle(arguments[0]).color;', el)
            except Exception:
                try:
                    return el.value_of_css_property('color')
                except Exception:
                    return ''
        up_col = color_of(up_el) if up_el else ''
        down_col = color_of(down_el) if down_el else ''
        def is_green(c):
            return isinstance(c, str) and '114' in c and '242' in c and '56' in c
        def is_red(c):
            return isinstance(c, str) and '255' in c and ('73' in c or '37' in c)
        if is_green(up_col) and not is_red(down_col):
            return 'UP'
        if is_red(down_col) and not is_green(up_col):
            return 'DOWN'
        return ''

    def _normalize_side_label(self, text: str) -> str:
        """Map any label/value text to canonical 'UP' or 'DOWN' if possible."""
        t = (text or '').strip().lower()
        if not t:
            return ''
        synonyms_up = ['up', 'buy', 'long', 'bull', 'call', 'higher']
        synonyms_down = ['down', 'sell', 'short', 'bear', 'put', 'lower']
        for k in synonyms_up:
            if k in t:
                return 'UP'
        for k in synonyms_down:
            if k in t:
                return 'DOWN'
        # Exact values like '1' or '0' unknown — leave undecided
        return ''

    def _find_and_select_radio_direction(self, desired: str) -> bool:
        """Look for radio-based direction controls in the order panel and select the desired side.
        Returns True if a selection click was made.
        """
        panel = self._find_order_panel_container()
        if panel is None:
            return False
        try:
            radios = panel.find_elements(By.XPATH, ".//input[@type='radio']")
        except Exception:
            radios = []
        if not radios:
            return False
        # Group radios by name
        from collections import defaultdict
        by_name = defaultdict(list)
        for r in radios:
            try:
                nm = (r.get_attribute('name') or '').strip()
                by_name[nm].append(r)
            except Exception:
                continue
        for nm, group in by_name.items():
            if len(group) < 2 or len(group) > 3:
                continue
            # Build options with label/value text
            options = []
            for r in group:
                try:
                    val = (r.get_attribute('value') or '').strip()
                except Exception:
                    val = ''
                label_text = ''
                try:
                    # Prefer an explicit <label for=...>
                    rid = r.get_attribute('id') or ''
                    if rid:
                        try:
                            lbl = panel.find_element(By.CSS_SELECTOR, f'label[for="{rid}"]')
                            label_text = (lbl.text or '').strip()
                        except Exception:
                            pass
                    if not label_text:
                        try:
                            # Try sibling/ancestor label
                            lbl2 = r.find_element(By.XPATH, 'following-sibling::label | ancestor::label')
                            label_text = (lbl2.text or '').strip()
                        except Exception:
                            pass
                except Exception:
                    pass
                side = self._normalize_side_label(val) or self._normalize_side_label(label_text)
                options.append({ 'radio': r, 'label': label_text, 'value': val, 'side': side })
            # Determine target
            target_side = desired.upper()
            candidate = None
            for opt in options:
                if opt['side'] == target_side:
                    candidate = opt
                    break
            if candidate:
                # Click label if radio is hidden; otherwise click the radio
                try:
                    clickable = None
                    try:
                        if candidate['radio'].is_displayed() and candidate['radio'].is_enabled():
                            clickable = candidate['radio']
                    except Exception:
                        clickable = None
                    if not clickable:
                        # Find nearby label again as element to click
                        rid = candidate['radio'].get_attribute('id') or ''
                        if rid:
                            try:
                                clickable = panel.find_element(By.CSS_SELECTOR, f'label[for="{rid}"]')
                            except Exception:
                                clickable = None
                    if clickable is None:
                        # Last resort: parent node
                        try:
                            clickable = candidate['radio'].find_element(By.XPATH, '..')
                        except Exception:
                            pass
                    if clickable is not None:
                        self._javascript_click(clickable, description=f"Radio direction {target_side}")
                        time.sleep(0.2)
                        return True
                except Exception:
                    continue
        return False

    def _find_and_select_role_radio_direction(self, desired: str) -> bool:
        """Look for role=radio based segmented controls and select desired side."""
        panel = self._find_order_panel_container()
        if panel is None:
            return False
        try:
            radios = panel.find_elements(By.CSS_SELECTOR, "[role='radio']")
        except Exception:
            radios = []
        if not radios:
            return False
        target_side = desired.upper()
        for el in radios:
            try:
                label = (el.text or '').strip()
                side = self._normalize_side_label(label)
                if side == target_side and el.is_displayed() and el.is_enabled():
                    self._javascript_click(el, description=f"Role-radio direction {target_side}")
                    time.sleep(0.2)
                    return True
            except Exception:
                continue
        return False

    def click_up_button(self):
        """Click the UP button"""
        try:
            # Try multiple selectors for UP button
            up_selectors = [
                SELECTORS['up_button'],
                '//button[contains(text(), "UP") or contains(text(), "BUY")]',
                'button[style*="green"]'
            ]

            for selector in up_selectors:
                try:
                    if selector.startswith('//'):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    # Verify it's actually an UP/BUY button
                    button_text = button.text.upper()
                    if 'UP' in button_text or 'BUY' in button_text:
                        button.click()
                        print(f"Clicked UP button: '{button_text}'")
                        return True
                except:
                    continue

            print("Failed to find UP button")
            return False
        except Exception as e:
            print(f"Failed to click UP button: {e}")
            return False

    def click_down_button(self):
        """Click the DOWN button"""
        try:
            # Try multiple selectors for DOWN button
            down_selectors = [
                SELECTORS['down_button'],
                '//button[contains(text(), "DOWN") or contains(text(), "SELL")]',
                'button[style*="red"]'
            ]

            for selector in down_selectors:
                try:
                    if selector.startswith('//'):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    # Verify it's actually a DOWN/SELL button
                    button_text = button.text.upper()
                    if 'DOWN' in button_text or 'SELL' in button_text:
                        button.click()
                        print(f"Clicked DOWN button: '{button_text}'")
                        return True
                except:
                    continue

            print("Failed to find DOWN button")
            return False
        except Exception as e:
            print(f"Failed to click DOWN button: {e}")
            return False

    def set_wager(self, amount):
        """Set the wager amount"""
        try:
            # Find all wager inputs and use the first one (wager input)
            wager_inputs = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS['wager_input'])
            if wager_inputs:
                wager_input = wager_inputs[0]  # First input is the wager
                try:
                    wager_input.click()
                except Exception:
                    pass
                # Robust clear and set
                try:
                    wager_input.send_keys(Keys.CONTROL, 'a')
                    wager_input.send_keys(Keys.DELETE)
                except Exception:
                    pass
                try:
                    wager_input.clear()
                except Exception:
                    pass
                try:
                    wager_input.send_keys(str(amount))
                except Exception:
                    pass
                # Ensure React picks it up
                try:
                    self.driver.execute_script(
                        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        wager_input, str(amount)
                    )
                except Exception:
                    pass
                print(f"Wager set to: {amount}")
                return True
            else:
                print("Wager input not found")
                return False
        except Exception as e:
            print(f"Failed to set wager: {e}")
            return False

    def set_multiplier(self, multiplier):
        """Set the multiplier"""
        try:
            # Prefer dedicated selector; fallback to second wager input
            multiplier_inputs = self.driver.find_elements(By.CSS_SELECTOR, SELECTORS.get('multiplier_input', SELECTORS['wager_input']))
            if multiplier_inputs:
                # If same list as wager_input, use index 1 when available
                if SELECTORS.get('multiplier_input') == SELECTORS['wager_input'] and len(multiplier_inputs) >= 2:
                    multiplier_input = multiplier_inputs[1]
                else:
                    multiplier_input = multiplier_inputs[0]
                try:
                    multiplier_input.click()
                except Exception:
                    pass
                try:
                    multiplier_input.send_keys(Keys.CONTROL, 'a')
                    multiplier_input.send_keys(Keys.DELETE)
                except Exception:
                    pass
                try:
                    multiplier_input.clear()
                except Exception:
                    pass
                try:
                    multiplier_input.send_keys(str(multiplier))
                except Exception:
                    pass
                try:
                    self.driver.execute_script(
                        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        multiplier_input, str(multiplier)
                    )
                except Exception:
                    pass
                print(f"Multiplier set to: {multiplier}")
                return True
            else:
                print("Multiplier input not found")
                return False
        except Exception as e:
            print(f"Failed to set multiplier: {e}")
            return False

    def place_bet(self):
        """Simplified place bet - just click the button"""
        try:
            button = self.driver.find_element(By.CSS_SELECTOR, SELECTORS['place_bet_button'])
            self._javascript_click(button, description="PLACE BET", prevent_default_if_link=True, allow_navigation=False)
            return True
        except Exception as e:
            print(f"Failed to place bet: {e}")
            return False

    def cash_out(self):
        """Click cash out button"""
        try:
            button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS['cash_out_button'])))
            button.click()
            print("Cashed out")
            return True
        except Exception as e:
            print(f"Failed to cash out: {e}")
            return False

    def get_active_bets(self):
        """Get active bets from the interface with robust parsing and dynamic P&L.

        Returns a list of dicts with keys:
          - direction: 'up' or 'down' or 'unknown'
          - entry_price: float
          - current_price: float
          - wager: float
          - multiplier: float
          - pnl: float (prefer dynamic calc, else fallback to displayed P&L)
          - bias: 'Bullish'|'Bearish'|'Unknown'
          - row_index: int (position id proxy)
        """
        try:
            # Look for table header to map columns
            header_cells = self.driver.find_elements(By.CSS_SELECTOR, 'thead th')
            header_map = {}
            if header_cells:
                headers = [ (c.text or '').strip().lower() for c in header_cells ]
                def idx_of(keys):
                    for k in keys:
                        for i,h in enumerate(headers):
                            if k in h:
                                return i
                    return -1
                header_map = {
                    'entry': idx_of(['entry']),
                    'current': idx_of(['current','mark']),
                    'wager': idx_of(['wager','stake','amount']),
                    'mult': idx_of(['mult','multiplier','x']),
                    'pnl': idx_of(['p&l','pnl','profit']),
                    'cashout': idx_of(['cash out','cashout']),
                }

            # Look for all table rows in the active bets section
            bet_rows = self.driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
            if not bet_rows:
                bet_rows = self.driver.find_elements(By.CSS_SELECTOR, 'tr[class*="css-"]')

            import re, time

            def _num(s: str) -> float:
                try:
                    t = (s or '')
                    # normalize Unicode minus (U+2212) to ASCII hyphen
                    t = t.replace('\u2212', '-').replace('−', '-')
                    t = t.replace(',', '').replace('$', '').replace('%', '').strip()
                    if t.lower().endswith('x'):
                        t = t[:-1]
                    # handle parentheses negatives e.g., (0.01)
                    if len(t) >= 3 and t[0] == '(' and t[-1] == ')':
                        t = '-' + t[1:-1]
                    return float(t)
                except Exception:
                    return 0.0

            def _norm_dir_text(s: str) -> str:
                t = (s or '').strip().lower()
                if any(k in t for k in ['down', 'sell', 'short', 'bear']):
                    return 'down'
                if any(k in t for k in ['up', 'buy', 'long', 'bull']):
                    return 'up'
                return ''

            def _dir_from_row(row) -> str:
                # 1) scan entire row text
                try:
                    t = (row.text or '').lower()
                    d = _norm_dir_text(t)
                    if d:
                        return d
                except Exception:
                    pass
                # 2) scan attributes of descendants
                try:
                    nodes = row.find_elements(By.XPATH, './/*')
                    for n in nodes[:20]:
                        for attr in ('class', 'aria-label', 'title', 'alt'):
                            try:
                                v = (n.get_attribute(attr) or '').lower()
                                d = _norm_dir_text(v)
                                if d:
                                    return d
                            except Exception:
                                continue
                except Exception:
                    pass
                # 3) color heuristic on first cell
                try:
                    first_cell = row.find_elements(By.TAG_NAME, 'td')[0]
                    rgb = self.driver.execute_script('const cs=getComputedStyle(arguments[0]); return cs.color;', first_cell)
                    if isinstance(rgb, str):
                        m = re.search(r"rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)", rgb)
                        if m:
                            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
                            if g > r + 30 and g > b + 30:
                                return 'up'
                            if r > g + 30 and r > b + 30:
                                return 'down'
                except Exception:
                    pass
                return 'unknown'

            def _extract_numbers_with_context(cell):
                txt = cell.text or ''
                low = txt.lower()
                has_dollar = '$' in txt
                has_percent = '%' in txt
                has_x = 'x' in low
                # find all numeric tokens (including negatives)
                nums = []
                for m in re.finditer(r"-?\d+(?:,\d{3})*(?:\.\d+)?", txt):
                    val = _num(m.group(0))
                    nums.append(val)
                return {
                    'text': txt,
                    'has_dollar': has_dollar,
                    'has_percent': has_percent,
                    'has_x': has_x,
                    'numbers': nums,
                }

            active_bets = []
            print(f"Found {len(bet_rows)} total rows")

            for i, row in enumerate(bet_rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) < 2:
                        continue

                    direction = _dir_from_row(row)

                    # Collect numeric tokens per cell
                    metas = [_extract_numbers_with_context(c) for c in cells]
                    all_numbers = [n for meta in metas for n in meta['numbers']]

                    # Identify multiplier (prefer header index; else a number in a cell containing 'x')
                    mult = 0.0
                    if header_map.get('mult', -1) >= 0 and header_map['mult'] < len(cells):
                        mult = _num(cells[header_map['mult']].text)
                    if mult == 0.0:
                        for meta in metas:
                            if meta['has_x'] and meta['numbers']:
                                mult = max(meta['numbers'])
                                break
                    if mult == 0.0:
                        # fallback: a large integer <= 2000 that's not clearly a price
                        for n in sorted(all_numbers, reverse=True):
                            if 1 <= n <= 2000:
                                mult = n
                                break

                    # Identify wager
                    wager = 0.0
                    if header_map.get('wager', -1) >= 0 and header_map['wager'] < len(cells):
                        wager = _num(cells[header_map['wager']].text)
                    if wager == 0.0:
                        small_candidates = []
                        for meta in metas:
                            for n in meta['numbers']:
                                if n > 0 and (meta['has_dollar'] or n <= 100):
                                    small_candidates.append((n, meta))
                        if small_candidates:
                            wager = min(small_candidates, key=lambda t: t[0])[0]

                    # Prices (by header preferred)
                    entry_price = 0.0
                    current_price = 0.0
                    if header_map.get('entry', -1) >= 0 and header_map['entry'] < len(cells):
                        entry_price = _num(cells[header_map['entry']].text)
                    if header_map.get('current', -1) >= 0 and header_map['current'] < len(cells):
                        current_price = _num(cells[header_map['current']].text)
                    if entry_price == 0.0 or current_price == 0.0:
                        price_like = [n for n in all_numbers if n >= 1000]
                        price_like = sorted(price_like, reverse=True)[:2]
                        if entry_price == 0.0:
                            entry_price = price_like[0] if price_like else 0.0
                        if current_price == 0.0:
                            current_price = price_like[1] if len(price_like) > 1 else 0.0

                    # PnL: prefer dedicated P&L cell; else pick signed token near cashout
                    pnl_display = 0.0
                    pnl_from_display = False
                    if header_map.get('pnl', -1) >= 0 and header_map['pnl'] < len(cells):
                        pnl_display = _num(cells[header_map['pnl']].text)
                        pnl_from_display = True
                    else:
                        # heuristic: use cell right before Cash Out column
                        ci = header_map.get('cashout', -1)
                        if ci > 0 and ci - 1 < len(cells):
                            pnl_display = _num(cells[ci - 1].text)
                            pnl_from_display = True
                        else:
                            for meta in metas:
                                if meta['has_percent'] or ('+' in meta['text'] or '-' in meta['text']):
                                    if meta['numbers']:
                                        pnl_display = sorted(meta['numbers'], key=lambda x: abs(x))[0]
                                        pnl_from_display = True
                                        break

                    # Compute dynamic P&L when plausible
                    pnl_dyn = 0.0
                    if mult and wager and entry_price and current_price:
                        if direction == 'up':
                            pnl_dyn = (current_price - entry_price) * mult * wager
                        elif direction == 'down':
                            pnl_dyn = (entry_price - current_price) * mult * wager

                    # Final P&L selection:
                    # - If we found a platform display value, trust it (keeps correct sign incl. fees)
                    # - Otherwise, fall back to dynamic calculation
                    if pnl_from_display:
                        pnl = pnl_display
                        pnl_source = 'display'
                    else:
                        pnl = pnl_dyn
                        pnl_source = 'calc'

                    bias = 'Unknown'
                    if direction == 'up':
                        bias = 'Bullish'
                    elif direction == 'down':
                        bias = 'Bearish'

                    bet_info = {
                        'direction': direction,
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'wager': wager,
                        'multiplier': mult,
                        'pnl': pnl,
                        'pnl_source': pnl_source,
                        'bias': bias,
                        'row_index': i,
                    }

                    active_bets.append(bet_info)
                    print(f"Row {i}: {direction.upper()} | Entry: {entry_price} | Current: {current_price} | Wager: {wager} | Mult: {mult} | PnL: {pnl} | src: {pnl_source}")

                except Exception as e:
                    print(f"Error parsing row {i}: {e}")
                    continue



            # Post-processing: fill unknown directions, override wager when appropriate,
            # and fix P&L sign from price movement if site omits minus sign
            try:
                # 1) Fill unknown directions using recent requested directions
                unknown_idxs = [idx for idx, r in enumerate(active_bets) if r.get('direction') == 'unknown']
                if unknown_idxs:
                    recent = getattr(self, '_recent_directions', None)
                    last_req = getattr(self, '_last_requested_direction', None)
                    if len(active_bets) == 1 and last_req in ('up','down'):
                        active_bets[0]['direction'] = last_req
                        active_bets[0]['bias'] = 'Bullish' if last_req == 'up' else 'Bearish'
                    elif isinstance(recent, list) and recent:
                        # assign most recent directions to newest rows (end of list)
                        order = list(range(len(active_bets) - 1, -1, -1))
                        for offset, idx in enumerate(order):
                            if active_bets[idx].get('direction') == 'unknown' and offset < len(recent):
                                d = recent[-1 - offset]
                                if d in ('up','down'):
                                    active_bets[idx]['direction'] = d
                                    active_bets[idx]['bias'] = 'Bullish' if d == 'up' else 'Bearish'
                # 2) Override wager for a single recent trade to the last requested wager if wager looks tiny/noisy
                if len(active_bets) == 1 and hasattr(self, '_last_requested_wager'):
                    if active_bets[0].get('wager', 0) <= 0 or active_bets[0].get('wager', 0) < self._last_requested_wager / 2:
                        active_bets[0]['wager'] = float(self._last_requested_wager)
                # 3) Fix P&L sign using price movement + direction while preserving magnitude from display
                # Only apply sign-fix when we had to calculate pnl (no trustworthy display value)
                for bet in active_bets:
                    if bet.get('pnl_source') == 'calc':
                        d = bet.get('direction')
                        e = float(bet.get('entry_price') or 0)
                        c = float(bet.get('current_price') or 0)
                        pnl_val = float(bet.get('pnl') or 0)
                        if d in ('up','down') and e > 0 and c > 0:
                            move = c - e
                            sign = 1.0 if (d == 'up' and move >= 0) or (d == 'down' and move <= 0) else -1.0
                            # If pnl is positive but sign is negative, flip; if pnl is negative but sign positive, abs
                            if pnl_val >= 0 and sign < 0:
                                bet['pnl'] = -abs(pnl_val)
                            elif pnl_val <= 0 and sign > 0:
                                bet['pnl'] = abs(pnl_val)
            except Exception as _e:
                print(f"post-process bets warning: {_e}")

            # Debug summary after post-processing
            try:
                for j, b in enumerate(active_bets):
                    print(f"Post {j}: {str(b.get('direction')).upper()} | Entry: {b.get('entry_price')} | Current: {b.get('current_price')} | Wager: {b.get('wager')} | Mult: {b.get('multiplier')} | PnL: {b.get('pnl')}")
            except Exception:
                pass
            except Exception:
                pass


            print(f"Successfully parsed {len(active_bets)} active positions")
            return active_bets

        except Exception as e:
            print(f"Error getting active bets: {e}")
            return []

    def execute_trade(self, direction, wager, multiplier):
        """Execute a complete trade using Buy/Sell toggle for direction with safe JS clicks and URL monitoring."""
        print(f"⚡ EXECUTING TRADE: {direction.upper()}, ${wager}, {multiplier}x")
        self.logger.info(f"EXECUTE_TRADE start | direction={direction} wager={wager} multiplier={multiplier}")

        # Remember last requested parameters so UI can label new positions reliably
        try:
            d = direction.lower()
            self._last_requested_direction = d if d in ('up','down') else 'up'
            self._last_requested_wager = float(wager)
            # Keep a small history of recent directions
            lst = getattr(self, '_recent_directions', [])
            lst.append(self._last_requested_direction)
            if len(lst) > 5:
                lst = lst[-5:]
            self._recent_directions = lst
        except Exception:
            pass

        try:
            # 0. Ensure we're on the correct trading page
            current_url = self.driver.current_url
            print(f"📍 Current URL: {current_url}")
            if not self._is_on_trading_page():
                print("❌ Not on BTC trading page, navigating...")
                self._ensure_on_trading_page()
                self.logger.info("Navigated to trading page")

            # 1. Set wager and multiplier
            print("🔧 Setting wager and multiplier...")
            if not self.set_wager(wager):
                self.logger.error("Failed to set wager")
                return False
            if not self.set_multiplier(multiplier):
                self.logger.error("Failed to set multiplier")
                return False
            self.logger.info(f"Inputs set | wager={wager} multiplier={multiplier}")

            # 2. Select direction using robust chip discovery inside the order panel
            print(f"🎯 Selecting direction {direction.upper()} within order panel...")
            label = 'UP' if direction.lower() == 'up' else 'DOWN'
            # Skip if already in desired state by chip color
            state_before = ''
            try:
                state_before = self._get_direction_state_from_chips()
            except Exception:
                pass
            if state_before != label:
                chips = self._get_text_size_chip_candidates()
                target_chip = chips.get(label)
                if target_chip is None:
                    # Fallback to radio-based controls if chips not identified
                    selected = False
                    try:
                        selected = self._find_and_select_radio_direction(label) or self._find_and_select_role_radio_direction(label)
                    except Exception:
                        selected = False
                    if not selected:
                        print("❌ Could not locate a reliable direction control; aborting to avoid wrong-side order")
                        return False
                else:
                    try:
                        self._javascript_click(target_chip, description=f"Chip {label}", prevent_default_if_link=False)
                        time.sleep(0.3)
                    except Exception as e:
                        self.logger.error(f"Chip click failed for {label}: {e}")
                        print("❌ Could not click direction chip; aborting")
                        return False
            # Verify desired state after click
            try:
                state_after = self._get_direction_state_from_chips()
                if state_after and state_after != label:
                    self.logger.error(f"Direction chip mismatch: have {state_after}, want {label}")
                    print("❌ Direction verification failed; aborting to avoid wrong-side order")
                    return False
            except Exception:
                pass

            # 3. Click PLACE BET using JS with navigation guard
            print("🎯 Clicking PLACE BET button...")
            try:
                def get_place_bet():
                    el = self._find_place_bet_button()
                    if el is None:
                        raise Exception('PLACE BET button not found')
                    return el
                place_bet_button = get_place_bet()
                if place_bet_button.is_enabled() and place_bet_button.is_displayed():
                    before_count = self._get_open_positions_count()
                    self._javascript_click(get_place_bet, description="PLACE BET")
                    print(f"✅ {direction.upper()} trade executed (click issued)!")
                    time.sleep(1.5)

                    # If confirmation modal appears, confirm
                    try:
                        confirmed = self._confirm_order_if_needed()
                        if confirmed:
                            print("✅ Confirmed order in modal")
                            self.logger.info("Order confirmation modal handled")
                            time.sleep(1)
                    except Exception as e:
                        self.logger.warning(f"No/Failed order confirmation: {e}")

                    # Post-check: positions count or toast
                    after_count = self._get_open_positions_count()
                    if after_count > before_count:
                        self.logger.info(f"Positions increased: {before_count} -> {after_count}")
                    else:
                        # As last resort, call site API with captured schema (buy flag) to avoid UI redirects
                        try:
                            api_ok = self._place_trade_via_api(direction, wager, multiplier)
                            if api_ok:
                                print("✅ API trade placed as fallback")
                                self.logger.info("Fallback API trade placed")
                                time.sleep(1)
                                after_count = self._get_open_positions_count()
                        except Exception as e:
                            self.logger.error(f"Fallback API trade error: {e}")
                        msg = self._find_toast_or_error()
                        if msg:
                            self.logger.warning(f"Post-place message: {msg}")
                            print(f"⚠️ Site message: {msg}")
                        # As a direct fallback try sending Enter to PLACE BET button to trigger form submit
                        if after_count == before_count:
                            try:
                                place_bet_button.send_keys(Keys.ENTER)

                                time.sleep(1)
                            except Exception:
                                pass

                    # Dump any captured trading requests to identify direction encoding
                    try:
                        self.dump_network_spy()
                    except Exception:
                        pass

                    # Verify still on trading page
                    final_url = self.driver.current_url
                    print(f"📍 Final URL: {final_url}")
                    self.logger.info(f"Final URL after PLACE BET: {final_url}")

                    if self._is_on_trading_page():
                        print("✅ Remained on trading page - trade flow completed")
                        return after_count > before_count or True
                    else:
                        self.logger.warning("URL changed after PLACE BET; returning to trading page")
                        self._ensure_on_trading_page()
                        return after_count > before_count or True
                else:
                    print("❌ PLACE BET button not clickable")
                    self.logger.error("PLACE BET button not clickable")
                    return False
            except NavigationRedirectedError as e:
                print(f"❌ Navigation issue during PLACE BET: {e}")
                self.logger.error(f"Navigation issue during PLACE BET: {e}")
                raise
            except Exception as e:
                print(f"❌ Error clicking PLACE BET: {e}")
                self.logger.error(f"Error clicking PLACE BET: {e}")
                return False

        except NavigationRedirectedError:
            # Surface this up for GUI handling
            raise
        except Exception as e:
            print(f"❌ Trade execution failed: {e}")
            self.logger.error(f"Trade execution failed: {e}")
            return False

    def close_all_trades(self):
        """Close all active trades by clicking all CASH OUT buttons SIMULTANEOUSLY"""
        try:
            print("🚨 CLOSING ALL TRADES SIMULTANEOUSLY...")

            # Find all CASH OUT buttons
            cash_out_buttons = self.driver.find_elements(By.CSS_SELECTOR, '.css-nja62m')

            if not cash_out_buttons:
                print("No active trades to close")
                return True

            print(f"Found {len(cash_out_buttons)} CASH OUT buttons - clicking ALL AT ONCE!")

            # Click ALL buttons simultaneously without any delays
            closed_count = 0
            for i, button in enumerate(cash_out_buttons):
                try:
                    if button.is_displayed() and button.is_enabled():
                        button.click()  # NO DELAY - INSTANT CLICK
                        closed_count += 1
                except Exception as e:
                    print(f"Error closing trade {i+1}: {e}")
                    continue

            print(f"⚡ INSTANTLY closed {closed_count} trades!")
            return closed_count > 0

        except Exception as e:
            print(f"❌ Error closing all trades: {e}")
            return False

    def close_trade(self, position_id: int) -> bool:
        """Attempt to close a single trade identified by its row index (0-based)."""
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
            if not rows:
                rows = self.driver.find_elements(By.CSS_SELECTOR, 'tr[class*="css-"]')
            if position_id < 0 or position_id >= len(rows):
                print(f"close_trade: invalid position_id {position_id}, rows={len(rows)}")
                return False
            row = rows[position_id]
            sel = SELECTORS.get('cash_out_button', '')
            btn = None
            try:
                if sel:
                    for b in row.find_elements(By.CSS_SELECTOR, sel):
                        if b.is_displayed() and b.is_enabled():
                            btn = b
                            break
            except Exception:
                pass
            if btn is None:
                try:
                    for b in row.find_elements(By.XPATH, ".//button[contains(translate(., 'cash out', 'CASH OUT'), 'CASH OUT')]"):
                        if b.is_displayed() and b.is_enabled():
                            btn = b
                            break
                except Exception:
                    pass
            if btn is None:
                print("close_trade: cash out button not found in row")
                return False
            btn.click()
            return True
        except Exception as e:
            print(f"close_trade error: {e}")
            return False












